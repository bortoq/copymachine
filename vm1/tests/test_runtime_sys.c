#define _POSIX_C_SOURCE 200809L
/*
 * Unit tests for the channel frame (SYS + pre-bound device channels).
 *
 * Exercises sys_ctrl directly: data copies through device channels, SEEK/
 * FSTAT/IOCTL control through SYS, CLOSE (of a device channel and of SYS
 * itself -> isolation), the answer available after the request tick,
 * and the seed load.
 */
#include "../src/space.h"
#include "../src/sys_ctrl.h"
#include "../src/proto_gen.h"
#include <assert.h>
#include <errno.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

static int failures = 0;

#define CHECK(cond) do { if(!(cond)) { \
  fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond); ++failures; } } while(0)

/* device bytes live in space by the same convention bitcpy uses: the
 * first bit of a byte is its high bit (see bitcopy.c) */
static void fill_bytes(size addr, const char *s, size n)
{
  size i;
  for(i = 0; i < n; ++i)
    bitcpy(CHAR_BIT, s + i, 0, space, (size_t)(addr + i * CHAR_BIT));
}

static void read_bytes(size addr, char *s, size n)
{
  bitcpy((size_t)(n * CHAR_BIT), space, (size_t)addr, s, 0);
}

static void clear_proc(void)
{
  size_t i;
  for(i = 0; i < proc_n; ++i)
    processor[i][0] = processor[i][1] = processor[i][2] = 0;
}

static size SYS_POS(void) { return (size)space_nbits; }
static size IN_POS(void)  { return (size)space_nbits + 1; }
static size OUT_POS(void) { return (size)space_nbits + 2; }

/* send one control request through SYS; answer decoded into rsp */
static void send(size req_addr, size rsp_addr, const size *req, size *rsp)
{
  size v[REQ_NFIELDS];
  unsigned i;
  clear_proc();
  for(i = 0; i < REQ_NFIELDS; ++i)
    v[i] = req[i];
  sys_encode_req(req_addr, v);
  processor[0][0] = sys_req_bits();
  processor[0][1] = SYS_POS();          /* dst = SYS: request */
  processor[0][2] = req_addr;
  sys_tick();
  clear_proc();
  processor[1][0] = sys_rsp_bits();
  processor[1][1] = rsp_addr;           /* dst = rsp buffer */
  processor[1][2] = SYS_POS();          /* src = SYS: answer read */
  sys_tick();
  sys_decode_rsp(rsp_addr, rsp);
}

/*
 * EXEC request: the record plus the command bytes in the same
 * half-interval [req_addr, req_addr+nbits). nbits==0 means the exact
 * size REQ_BITS + 8*L; any other value is used verbatim (for the
 * malformed case). The answer is read in the following tick.
 */
static void exec_send(size req_addr, size rsp_addr, const char *cmd,
                      size len, size nbits, size *rsp)
{
  size v[REQ_NFIELDS];
  clear_proc();
  memset(v, 0, sizeof v);
  v[0] = OP_EXEC;
  v[3] = len;                           /* arg = command length, bytes */
  sys_encode_req(req_addr, v);
  fill_bytes((size)(req_addr + sys_req_bits()), cmd, len);
  processor[0][0] = nbits ? nbits
                          : (size)(sys_req_bits() + len * CHAR_BIT);
  processor[0][1] = SYS_POS();
  processor[0][2] = req_addr;
  sys_tick();
  clear_proc();
  processor[1][0] = sys_rsp_bits();
  processor[1][1] = rsp_addr;
  processor[1][2] = SYS_POS();
  sys_tick();
  sys_decode_rsp(rsp_addr, rsp);
}

/* --- error paths: errno propagation and FSTAT state ------------------- */

/*
 * FSTAT must return the size together with the state of the channel's
 * last data operation. The status of a failed read/write has to survive
 * the fstat itself, and sys_device_pos must name the seeded channels.
 */
static void test_errors(void)
{
  char *argv[] = { "space", "-s", "65520", "-p", "8" };
  FILE *full = fopen("/dev/full", "w");   /* writes fail with ENOSPC */
  FILE *dir = fopen(".", "r");            /* reads fail with EISDIR */
  size req_addr = 1000, rsp_addr = 2000, data = 9000;
  size req[REQ_NFIELDS], rsp[RSP_NFIELDS];

  if(full != NULL)
    setvbuf(full, NULL, _IONBF, 0);
  channel_in = dir;                       /* read error source */
  channel_out = full;                     /* write error sink */
  parse_config(5, argv);
  init_space();

  /* device positions come from the XDEV table in order */
  CHECK(sys_device_pos(0) == IN_POS());
  CHECK(sys_device_pos(1) == OUT_POS());
  CHECK(sys_device_pos(2) == (size)space_nbits + 3);

  /* write error (ENOSPC): status visible through FSTAT afterwards */
  if(full != NULL)
  {
    fill_bytes(data, "X", 1);
    clear_proc();
    processor[0][0] = 8;
    processor[0][1] = OUT_POS();
    processor[0][2] = data;
    sys_tick();
    memset(req, 0, sizeof req);
    req[0] = OP_FSTAT; req[1] = OUT_POS();
    send(req_addr, rsp_addr, req, rsp);
    CHECK(rsp[1] == (size)ENOSPC);
    CHECK(rsp[4] == 0);                   /* nothing moved */
  }

  /* read error (EISDIR): same status path for input */
  if(dir != NULL)
  {
    clear_proc();
    processor[0][0] = 8;
    processor[0][1] = data;
    processor[0][2] = IN_POS();
    sys_tick();
    memset(req, 0, sizeof req);
    req[0] = OP_FSTAT; req[1] = IN_POS();
    send(req_addr, rsp_addr, req, rsp);
    CHECK(rsp[1] == (size)EISDIR);
  }

  /* CLOSE of a position that is not a channel -> EBADF */
  memset(req, 0, sizeof req);
  req[0] = OP_CLOSE; req[1] = (size)space_nbits - 1;
  send(req_addr, rsp_addr, req, rsp);
  CHECK(rsp[0] == OP_CLOSE);
  CHECK(rsp[1] == (size)EBADF);

  if(full != NULL) fclose(full);
  if(dir != NULL) fclose(dir);
  free(space);
  free(processor);
  free(instructions);
}

/* Slot permutations: transfer, request, then committed response read. */
static void test_tick_boundaries(void)
{
  unsigned mode, a, b, c;
  for(mode = 0; mode < 5; ++mode)
    for(a = 0; a < 3; ++a)
      for(b = 0; b < 3; ++b)
        for(c = 0; c < 3; ++c)
        {
          char *argv[] = { "space", "-s", "65520", "-p", "8" };
          FILE *in, *out;
          size req[REQ_NFIELDS] = {0}, rsp[RSP_NFIELDS];
          char got[4] = {0};
          int writing = mode >= 2;
          if(a == b || a == c || b == c) continue;
          in = mode == 1 ? fopen(".", "r") : tmpfile();
          out = mode == 3 ? fopen("/dev/full", "w") : tmpfile();
          if(mode == 4)
          {
            int pipe_fd[2];
            fclose(out);
            CHECK(pipe(pipe_fd) == 0);
            close(pipe_fd[0]);
            out = fdopen(pipe_fd[1], "w");
          }
          CHECK(in != NULL && out != NULL);
          if(in == NULL || out == NULL) exit(1);
          setvbuf(out, NULL, _IONBF, 0);
          if(mode == 0) { fwrite("AB", 1, 2, in); rewind(in); }
          channel_in = in; channel_out = out;
          parse_config(5, argv);
          init_space();
          clear_proc();
          fill_bytes(9000, "XYZ", 3);
          req[0] = OP_FSTAT;
          req[1] = writing ? OUT_POS() : IN_POS();
          sys_encode_req(1000, req);
          processor[a][0] = 24;
          processor[a][1] = writing ? OUT_POS() : 9000;
          processor[a][2] = writing ? 9000 : IN_POS();
          sys_tick();
          clear_proc();
          processor[b][0] = sys_req_bits();
          processor[b][1] = SYS_POS(); processor[b][2] = 1000;
          processor[c][0] = sys_rsp_bits();
          processor[c][1] = 2000; processor[c][2] = SYS_POS();
          sys_tick();
          sys_decode_rsp(2000, rsp);
          for(unsigned k=0;k<RSP_NFIELDS;++k) CHECK(rsp[k]==0);
          clear_proc();
          processor[c][0]=sys_rsp_bits();
          processor[c][1]=2000; processor[c][2]=SYS_POS();
          sys_tick(); sys_decode_rsp(2000,rsp);
          CHECK(rsp[0] == OP_FSTAT);
          CHECK(rsp[1] == (size)(mode == 1 ? EISDIR : mode == 3 ? ENOSPC : mode == 4 ? EPIPE : 0));
          CHECK(rsp[4] == (size)(mode == 0 ? 2 : mode == 2 ? 3 : 0));
          CHECK(rsp[5] == (size)(mode == 0));
          if(mode == 0) { read_bytes(9000, got, 3); CHECK(memcmp(got, "ABZ", 3) == 0); }
          if(mode == 2) { rewind(out); CHECK(fread(got, 1, 4, out) == 3); CHECK(memcmp(got, "XYZ", 3) == 0); }
          fclose(in); fclose(out); free(space); free(processor);
  free(instructions);
        }
}

/* --- boot path ------------------------------------------------------- */

typedef struct { FILE *f; unsigned char byte; int nbit; } bitwriter;

static void bw_put(bitwriter *w, size v, size n)
{
  size k;
  for(k = 0; k < n; ++k)
  {
    w->byte = (unsigned char)((w->byte << 1) | (unsigned char)((v >> k) & 1));
    if(++w->nbit == 8) { fputc(w->byte, w->f); w->byte = 0; w->nbit = 0; }
  }
}

static void bw_flush(bitwriter *w)
{
  if(w->nbit) { w->byte <<= (8 - w->nbit); fputc(w->byte, w->f); }
  w->byte = 0; w->nbit = 0;
}

/* a program of proc_n instructions: instruction 1 copies 7 bits from
 * 54321 to 12345, the rest are NOPs */
static void write_boot_program(FILE *f)
{
  bitwriter w = { f, 0, 0 };
  size i, a = address_bits;
  for(i = 0; i < (size)proc_n; ++i)
  {
    if(i == 1) { bw_put(&w,12345,a); bw_put(&w,12352,a); bw_put(&w,54321,a); bw_put(&w,54328,a); }
    else { for(unsigned k=0;k<4;k++) bw_put(&w,0,a); }
  }
  bw_flush(&w);
  fflush(f);
}

static void test_boot(void)
{
  char *argv[] = { "space", "-s", "65520", "-p", "8" };
  FILE *prog = tmpfile();
  FILE *out = tmpfile();
  size isz, a;

  parse_config(5, argv);
  channel_in = prog;
  channel_out = out;
  init_space();                       /* binds proc as the stdin channel */
  isz = instruction_size; a = address_bits;

  write_boot_program(prog);
  rewind(prog);

  /* tick 1: the seed copy loads the program from the stdin channel */
  CHECK(computation() == 1);
  CHECK(space_get(isz,a)==12345);
  CHECK(space_get(isz+a,a)==12352);
  CHECK(space_get(isz+2*a,a)==54321);
  CHECK(space_get(isz+3*a,a)==54328);
  /* tick 2: instruction 1 runs the copy */
  space_put(7, 85, 54321);
  CHECK(computation() == 1);
  CHECK(space_get(12345, 7) == 85);
  fclose(prog);
  fclose(out);
  free(space);
  free(processor);
  free(instructions);
}

/* --- EXEC: run a host program given as bytes from the space -------- */

static void test_exec(void)
{
  char *argv[] = { "space", "-s", "65520", "-p", "8" };
  FILE *in = tmpfile(), *out = tmpfile();
  size req_addr = 1000, rsp_addr = 2000;
  size rsp[RSP_NFIELDS];
  char marker[64];

  channel_in = in;
  channel_out = out;
  parse_config(5, argv);
  init_space();
  snprintf(marker, sizeof marker, "/tmp/space_exec_marker_%ld",
           (long)getpid());
  remove(marker);

  /* true -> status 0 */
  exec_send(req_addr, rsp_addr, "true", 4, 0, rsp);
  CHECK(rsp[0] == OP_EXEC);
  CHECK(rsp[1] == 0);

  /* exit 3 -> status 3; the raw wait status is in size */
  exec_send(req_addr, rsp_addr, "exit 3", 6, 0, rsp);
  CHECK(rsp[0] == OP_EXEC);
  CHECK(rsp[1] == 3);
  CHECK(WEXITSTATUS((int)rsp[3]) == 3);

  /* side effect: a shell redirection creates the marker file */
  {
    char cmd[128];
    snprintf(cmd, sizeof cmd, ": > %s", marker);
    exec_send(req_addr, rsp_addr, cmd, (size)strlen(cmd), 0, rsp);
    CHECK(rsp[1] == 0);
    {
      FILE *f = fopen(marker, "r");
      CHECK(f != NULL);
      if(f != NULL) fclose(f);
    }
  }

  /* malformed: n < REQ_BITS + 8*L -> EINVAL */
  exec_send(req_addr, rsp_addr, "x", 1, sys_req_bits(), rsp);
  CHECK(rsp[0] == OP_EXEC);
  CHECK(rsp[1] == (size)EINVAL);

  remove(marker);
  fclose(in);
  fclose(out);
  free(space);
  free(processor);
  free(instructions);
}

/* --- EXEC with a byte-misaligned command start (odd a) -------------- */

static void test_exec_align(void)
{
  /* -s 30000 -> a=15, so REQ_BITS = 135 is not a whole number of bytes:
   * the command starts at a bit offset that is not a byte boundary.
   * A multi-byte command must still come back byte-exact. */
  char *argv[] = { "space", "-s", "30000", "-p", "8" };
  FILE *in = tmpfile(), *out = tmpfile();
  size req_addr = 1000, rsp_addr = 2000;
  size rsp[RSP_NFIELDS];

  channel_in = in;
  channel_out = out;
  parse_config(5, argv);
  init_space();

  CHECK(sys_req_bits() % CHAR_BIT != 0);
  exec_send(req_addr, rsp_addr, "exit 42", 7, 0, rsp);
  CHECK(rsp[0] == OP_EXEC);
  CHECK(rsp[1] == 42);

  fclose(in);
  fclose(out);
  free(space);
  free(processor);
  free(instructions);
}

/* --- SEEK on a seekable file: position affects the next write ----- */

static void test_seek_file(void)
{
  char *argv[] = { "space", "-s", "65520", "-p", "8" };
  FILE *out = tmpfile(), *in = tmpfile();
  size req_addr = 1000, rsp_addr = 2000, data = 8000;
  size req[REQ_NFIELDS], rsp[RSP_NFIELDS];
  unsigned char got[16];

  channel_in = in;
  channel_out = out;
  parse_config(5, argv);
  init_space();

  /* write "ABC" to the stdout channel (a seekable file) */
  fill_bytes(data, "ABC", 3);
  clear_proc();
  processor[0][0] = 3 * CHAR_BIT;
  processor[0][1] = OUT_POS();
  processor[0][2] = data;
  sys_tick();

  /* SEEK to offset 1, then write "xy" -> overwrites to "Axy" */
  memset(req, 0, sizeof req);
  req[0] = OP_SEEK;
  req[1] = OUT_POS();
  req[3] = 0;                         /* whence SEEK_SET */
  req[4] = 1;                         /* offset */
  send(req_addr, rsp_addr, req, rsp);
  CHECK(rsp[0] == OP_SEEK);
  CHECK(rsp[1] == 0);

  fill_bytes(data, "xy", 2);
  clear_proc();
  processor[0][0] = 2 * CHAR_BIT;
  processor[0][1] = OUT_POS();
  processor[0][2] = data;
  sys_tick();
  fflush(out);
  rewind(out);
  CHECK(fread(got, 1, 16, out) == 3);
  CHECK(got[0] == 'A' && got[1] == 'x' && got[2] == 'y');

  fclose(in);
  fclose(out);
  free(space);
  free(processor);
  free(instructions);
}

int main(void)
{
  char *argv[] = { "space", "-s", "65520", "-p", "8" };
  FILE *out = tmpfile();
  FILE *in = tmpfile();
  size req_addr = 1000, rsp_addr = 2000, buf = 8000, data = 9000;
  size req[REQ_NFIELDS], rsp[RSP_NFIELDS];
  unsigned char got[16];

  channel_in = in;
  channel_out = out;
  parse_config(5, argv);
  init_space();

  /* --- channels present at start --- */
  CHECK(sys_is_channel(SYS_POS()));
  CHECK(sys_is_channel(IN_POS()));
  CHECK(sys_is_channel(OUT_POS()));
  CHECK(!sys_is_channel((size)space_nbits - 1));
  CHECK(!sys_is_channel(SYS_POS() + 1 + PROTO_NDEVS));
  CHECK(sys_req_bits() > 0 && sys_rsp_bits() > 0);

  /* --- data write: copy 3 bytes from space to the stdout channel --- */
  fill_bytes(data, "ABC", 3);
  clear_proc();
  processor[0][0] = 3 * CHAR_BIT;
  processor[0][1] = OUT_POS();        /* dst = channel: write out */
  processor[0][2] = data;
  sys_tick();
  fflush(out);
  rewind(out);
  CHECK(fread(got, 1, 16, out) == 3);
  CHECK(memcmp(got, "ABC", 3) == 0);

  /* --- data read: copy 4 bytes from the stdin channel into space --- */
  fwrite("WXYZ", 1, 4, in);
  fflush(in);
  rewind(in);
  clear_proc();
  processor[0][0] = 4 * CHAR_BIT;
  processor[0][1] = buf;              /* dst = space buffer */
  processor[0][2] = IN_POS();         /* src = channel: read in */
  sys_tick();
  read_bytes(buf, (char *)got, 4);
  CHECK(memcmp(got, "WXYZ", 4) == 0);

  /* --- FSTAT stdin: size 4, moved 4 (state via SYS) --- */
  memset(req, 0, sizeof req);
  req[0] = OP_FSTAT;
  req[1] = IN_POS();
  send(req_addr, rsp_addr, req, rsp);
  CHECK(rsp[0] == OP_FSTAT);
  CHECK(rsp[1] == 0);                 /* status ok */
  CHECK(rsp[3] == 4);                 /* size */
  CHECK(rsp[4] == 4);                 /* moved of the last read */
  CHECK(rsp[5] == 0);                 /* eof not set */

  /* --- SEEK stdout to offset 0 --- */
  memset(req, 0, sizeof req);
  req[0] = OP_SEEK;
  req[1] = OUT_POS();
  req[3] = 0;                         /* whence SEEK_SET */
  req[4] = 0;                         /* offset */
  send(req_addr, rsp_addr, req, rsp);
  CHECK(rsp[0] == OP_SEEK);
  CHECK(rsp[1] == 0);

  /* --- unknown op -> EINVAL --- */
  memset(req, 0, sizeof req);
  req[0] = 999;
  send(req_addr, rsp_addr, req, rsp);
  CHECK(rsp[1] != 0);

  /* --- CLOSE stdout: position stops being a channel, data copy is a noop --- */
  memset(req, 0, sizeof req);
  req[0] = OP_CLOSE;
  req[1] = OUT_POS();
  send(req_addr, rsp_addr, req, rsp);
  CHECK(rsp[0] == OP_CLOSE);
  CHECK(rsp[1] == 0);
  CHECK(!sys_is_channel(OUT_POS()));

  /* a closed device channel is gone for control too: FSTAT -> EBADF */
  memset(req, 0, sizeof req);
  req[0] = OP_FSTAT;
  req[1] = OUT_POS();
  send(req_addr, rsp_addr, req, rsp);
  CHECK(rsp[0] == OP_FSTAT);
  CHECK(rsp[1] == (size)EBADF);

  /* --- CLOSE SYS: isolation (no control, no status possible) --- */
  memset(req, 0, sizeof req);
  req[0] = OP_CLOSE;
  req[1] = SYS_POS();
  clear_proc();
  sys_encode_req(req_addr, (size[REQ_NFIELDS]){OP_CLOSE, SYS_POS(), 0, 0, 0});
  processor[0][0] = sys_req_bits();
  processor[0][1] = SYS_POS();
  processor[0][2] = req_addr;
  sys_tick();
  CHECK(!sys_is_channel(SYS_POS()));

  /* --- after isolation, a SYS request is silently ignored --- */
  clear_proc();
  processor[0][0] = sys_req_bits();
  processor[0][1] = SYS_POS();
  processor[0][2] = req_addr;
  sys_tick();                         /* must not crash, no channel served */
  CHECK(!sys_is_channel(SYS_POS()));

  fclose(out);
  fclose(in);
  free(space);
  free(processor);
  free(instructions);

  test_errors();
  test_tick_boundaries();
  test_boot();
  test_exec();
  test_exec_align();
  test_seek_file();

  if(failures) { fprintf(stderr, "%d FAILURES\n", failures); return 1; }
  backend_shutdown(); sys_shutdown();
  printf("sys: all unit checks passed\n");
  return 0;
}

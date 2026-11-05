#!/bin/sh
# The tables of programs/forth.tw between "begin generated" and "end generated" (23.15), made from programs/forth.def.
#   sh tower/programs/forth_gen.sh            writes the tables to stdout
#   sh tower/programs/forth_gen.sh -w         puts them into programs/forth.tw
# No Python: awk. The text of the pool goes in strings of 7 bytes (a table of 56 bits is 87 % full: the stride is 64).
D=$(dirname "$0")
LC_ALL=C
export LC_ALL
gen() {
awk '
function rev8(c,   i, r) { r = 0; for (i = 0; i < 8; i++) { r = r * 2 + (c % 2); c = int(c / 2) } return r }
function ostr(c) { return c == 0 ? "\\0" : c == 10 ? "\\n" : c == 34 ? "\\\"" : c == 92 ? "\\\\" : chr[c] }
function seq(a, b,   i, s) { s = ""; for (i = a; i <= b; i++) s = s (i > a ? " " : "") i; return s }
function closet() {
  if (nt > 0) {
    pc[npool++] = 0
    while (npool % 7) pc[npool++] = 0
  }
}
BEGIN {
  for (i = 1; i < 256; i++) chr[i] = sprintf("%c", i)
  for (i = 1; i < 256; i++) ord[chr[i]] = i
  nk = split("plain colon semi if else then begin until repeat do loop leave exit recurse variable constant create paren bslash squote bchar tick macro uword uvar uconst execute", kn, " ")
  for (i = 1; i <= nk; i++) kind[kn[i]] = i - 1
  nt = 0; np = 0; nr = 0; mode = 0; npool = 0; npx = 0
}
/^\/\// { next }
/^%sys/ { for (i = 2; i <= NF; i++) sys[i - 1] = $i; nsys = NF - 1; next }
/^%px/ { npx++; pxn[npx] = $2; pxw[npx] = $3; next }
/^=words$/ { closet(); mode = 1; next }
mode == 0 && /^=/ { closet(); nt++; tname[nt] = substr($0, 2); tid[tname[nt]] = nt - 1; tstart[nt] = npool / 7; next }
mode == 0 {
  s = $0
  if (substr(s, length(s)) == "$") { s = substr(s, 1, length(s) - 1) } else { s = s "\n" }
  for (i = 1; i <= length(s); i++) { c = substr(s, i, 1); pc[npool++] = (c == "\n" ? 10 : ord[c]) }
  next
}
mode == 1 && NF >= 4 { np++; wn[np] = $1; wk[np] = $2; wr[np] = $3; wt[np] = $4; widx[$1] = np - 1; next }
END {
  if (npool > 10752) { print "forth_gen: the pool is too big: " npool > "/dev/stderr"; exit 1 }
  if (nt > 128 || np > 128) { print "forth_gen: too many templates or words" > "/dev/stderr"; exit 1 }
  # the classes of a byte (the index is the byte as the chain reads it: the bits reversed)
  printf ":cls table 8 8\n"
  for (i = 0; i < 256; i++) {
    c = rev8(i); v = 0
    if (c == 32 || c == 9 || c == 10 || c == 13) v += 1
    if (c == 0) v += 2
    if (c >= 48 && c <= 57) v += 4
    if (c == 45) v += 8
    if (c == 34) v += 16
    if (c == 41) v += 32
    if (c == 10) v += 64
    printf "%s%s", v, (i % 16 == 15 ? "\n" : " ")
  }
  printf ":pcl table 8 4\n"
  for (i = 0; i < 256; i++) {
    c = rev8(i); v = 0
    if (c == 0) v = 4
    if (c == 64) v = 8
    if (c == 126) v = 9
    if (c == 37) v = 10
    if (c == 94) v = 11
    printf "%s%s", v, (i % 16 == 15 ? "\n" : " ")
  }
  printf ":inc7 table 7 7\n%s 0\n", seq(1, 127)
  printf ":dec7 table 7 7\n127 %s\n", seq(0, 126)
  if (npool > 1536 * 7) { print "forth_gen: the pool is too big" > "/dev/stderr"; exit 1 }
  for (p = 0; p < 2; p++) {
    printf ":pool%d table %d 56\n", p, 10 - p
    for (e = 0; e < 1024 - 512 * p; e++) {
      s = ""
      for (k = 0; k < 7; k++) { x = (p * 1024 + e) * 7 + k; s = s ostr(x < npool ? pc[x] : 0) }
      printf "\"%s\"%s", s, (e % 6 == 5 ? "\n" : " ")
    }
    printf "\n"
  }
  printf ":tst table 7 12\n"
  for (i = 0; i < 128; i++) printf "%d%s", (i < nt ? tstart[i + 1] : 0), (i % 16 == 15 ? "\n" : " ")
  # the routines: the templates named in the third column, in the order of the first use
  nr = 0
  for (i = 1; i <= np; i++) if (wr[i] != "-" && wk[i] == "plain" && !(wr[i] in rid)) { nr++; rid[wr[i]] = nr; rname[nr] = wr[i] }
  printf ":rtt table 7 7\n0"
  for (i = 1; i < 128; i++) printf " %d", (i <= nr ? tid[rname[i]] : 0)
  printf "\n"
  printf ":pnm table 7 64\n"
  for (i = 0; i < 128; i++) {
    s = ""
    if (i < np) { n = wn[i + 1]; for (k = 0; k < 8 - length(n); k++) s = s "\\0"; for (k = 1; k <= length(n); k++) s = s ostr(ord[substr(n, k, 1)]) }
    else s = "\\0\\0\\0\\0\\0\\0\\0\\0"
    printf "\"%s\"%s", s, (i % 4 == 3 ? "\n" : " ")
  }
  printf ":pin table 7 17\n"
  for (i = 0; i < 128; i++) {
    v = 0
    if (i < np) {
      j = i + 1; k = kind[wk[j]]
      if (k == "") { print "forth_gen: bad kind " wk[j] > "/dev/stderr"; exit 1 }
      if (wk[j] == "macro") { r = wr[j] + 0; t = widx[wt[j]] }
      else { r = (wr[j] == "-" ? 0 : rid[wr[j]]); t = (wt[j] == "-" ? 0 : tid[wt[j]]) }
      v = k + 32 * r + 1024 * t
    }
    printf "%d%s", v, (i % 16 == 15 ? "\n" : " ")
  }
  printf ":npr data 7 %d\n:nrt data 7 %d\n", np, nr
  for (i = 1; i <= nsys; i++) { if (!(sys[i] in tid)) { print "forth_gen: no template " sys[i] > "/dev/stderr"; exit 1 } printf ":t_%s data 7 %d\n", sys[i], tid[sys[i]] }
  for (i = 1; i <= npx; i++) printf ":px_%s data 7 %d\n", pxn[i], widx[pxw[i]]
}
' "$D/forth.def"
}
if [ "$1" = "-w" ]; then
  T="$D/forth.tw"
  { sed -n '1,/^# --- begin generated$/p' "$T"; gen; sed -n '/^# --- end generated$/,$p' "$T"; } > "$T.new" && mv "$T.new" "$T"
else
  gen
fi

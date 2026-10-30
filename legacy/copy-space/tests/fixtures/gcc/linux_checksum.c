/* SPDX-License-Identifier: GPL-2.0-only */
#include <lib/checksum.c>

/* Independent byte-pair reference for the Internet checksum, expressed in
 * the target's little-endian representation. Avoid the word/carry algorithm
 * and alignment branches used by the original Linux implementation. */
static unsigned __attribute__((__noipa__)) reference(const unsigned char *p,
                                                    unsigned n, unsigned seed)
{
    unsigned sum=(seed & 65535U)+(seed >> 16);
    for (unsigned i=0; i<n; i+=2)
        sum+=p[i]+(i+1<n ? (unsigned)p[i+1]*256U : 0U);
    while (sum >> 16)
        sum=(sum & 65535U)+(sum >> 16);
    return (~sum)&65535U;
}

unsigned value(unsigned a, unsigned b)
{
    unsigned char bytes[96] __attribute__((aligned(4)));
    unsigned passed=0;
    for (unsigned i=0; i<sizeof(bytes); ++i)
        bytes[i]=(unsigned char)(i*37U+a*13U+b);
    for (unsigned offset=0; offset<4; ++offset)
        for (unsigned n=0; n<64; ++n) {
            unsigned seed=(n&1) ? 0xfffffff0U : 0x12345678U;
            passed+=(unsigned)(__force u16)ip_compute_csum(bytes+offset,n)
                    == reference(bytes+offset,n,0);
            passed+=(unsigned)(__force u16)csum_fold(csum_partial(bytes+offset,n,
                                                        (__force __wsum)seed))
                    == reference(bytes+offset,n,seed);
        }
    for (unsigned n=1; n<=32; ++n) {
        unsigned split=n & ~1U, size=n*2+1;
        __wsum partial=csum_partial(bytes+1,split,0);
        partial=csum_partial(bytes+1+split,size-split,partial);
        passed+=(unsigned)(__force u16)csum_fold(partial) == reference(bytes+1,size,0);
    }
    for (unsigned ihl=5; ihl<=15; ++ihl)
        passed+=(unsigned)(__force u16)ip_fast_csum(bytes,ihl) == reference(bytes,ihl*4,0);
    for (unsigned n=0; n<10; ++n) {
        unsigned len=n*1009U+7U, proto=n*23U;
        unsigned char pseudo[12]={192,0,2,1,198,51,100,2,0,(unsigned char)proto,
                                  (unsigned char)(len >> 8),(unsigned char)len};
        __sum16 actual=csum_tcpudp_magic(cpu_to_be32(0xc0000201U),
                                       cpu_to_be32(0xc6336402U),len,proto,
                                       (__force __wsum)0x12345678U);
        passed+=(unsigned)(__force u16)actual == reference(pseudo,12,0x12345678U);
    }
    return passed;
}

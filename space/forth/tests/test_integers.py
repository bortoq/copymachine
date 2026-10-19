"""Unsigned utilities: independent arithmetic and output edge cases."""
from guest_support import run_guest

lines = ['0 0 1 0 cc-du< . cr', '4294967295 0 0 1 cc-du< . cr',
         '0 1 4294967295 0 cc-du< . cr', '3 4 3 4 cc-du= . cr',
         '3 4 3 5 cc-du= . cr',
         '4294967295 0 1 0 cc-du+? . . . cr',
         '4294967295 4294967295 1 0 cc-du+? . . . cr',
         '0 1 1 0 cc-d- . . cr',
         '0 0 1 0 cc-d- . . cr',
         '0 4294967295 1 within . 1 4294967295 1 within . cr',
         '4294967295 u. cr', 'hex FFFFFFFF u. decimal cr',
         ': invalid-base 1 base ! 7 u. ;',
         "' invalid-base catch decimal . cr", 'depth . cr', 'bye']
expected = (b'-1 \n-1 \n0 \n-1 \n0 \n0 1 0 \n-1 0 0 \n'
            b'0 -1 \n-1 -1 \n-1 0 \n4294967295 \nFFFFFFFF \n-24 \n0 \n\n')
run_guest('integers', ['integers.fth'], lines, expected)

"""Nested evaluation restores parser state and propagates exceptions."""
from guest_support import run_guest

lines = [': calc s" 6 7 *" evaluate ;', 'calc . 123 . cr',
         ': make-word s" : evaluated-square dup * ;" evaluate ;',
         'make-word 9 evaluated-square . cr',
         ': inner-eval s" 99" evaluate ;',
         ': outer-eval s" inner-eval 1 +" evaluate ;', 'outer-eval . cr',
         ': fail-eval s" -55 throw" evaluate ;',
         "' fail-eval catch . 456 . cr", 'source-id . depth . cr', 'bye']
run_guest('evaluate', ['evaluate.fth'], lines,
          b'42 123 \n81 \n100 \n-55 456 \n0 0 \n\n')

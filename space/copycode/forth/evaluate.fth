\ SPDX-License-Identifier: MIT
\ Nested string evaluation using the guest parser/compiler.
\ SOURCE, >IN, SOURCE-ID and line state are restored even after THROW.
\ Source bytes must remain valid until return. Kernel include-depth limit: 16.
decimal
: evaluate ( addr bytes -- )
  dup 0< if -24 throw then
  source 2>r -1 push-source-id
  set-source 0 >in ! ['] interpret catch
  pop-source-id drop 2r> set-source throw ;

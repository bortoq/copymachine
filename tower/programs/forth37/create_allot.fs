create buf 16 allot variable v 3 constant three three 2 * 1+ constant seven
: main buf 16 0 do i 65 + over i + c! loop drop buf 16 0 do dup i + c@ emit loop drop seven 48 + emit ;

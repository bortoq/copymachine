: %t-hfill 1000 0 do cc-rows 32 cells 0 %hfill loop ;
: %t-hfill2 1000 0 do cc-rows 32 cells 0 %hfill cc-rows 32 cells 0 %hfill loop ;
: %t-hrow 1000 0 do cc-new-row %hrow drop loop ;
: %t-hrow2 1000 0 do cc-new-row %hrow drop cc-new-row %hrow drop loop ;
: %t-henc 1000 0 do 4 %henc drop loop ;
: %t-henc2 1000 0 do 4 %henc drop 4 %henc drop loop ;

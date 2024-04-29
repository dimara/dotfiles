Config { font = "xft:DejaVuSansMono:size=8:antialias=true"
       , bgColor = "#000000"
       , fgColor = "#C9A34E"
       , border = NoBorder
       , borderColor = "#000000"
       -- , position = Top
       -- https://hackage.haskell.org/package/xmobar-0.8/src/README.html
       -- , position = Static { xpos = 0 , ypos = 0, width = 1365, height = 16 }
       , position = Top,
       -- , position = Static { xpos = 0 , ypos = 0, width = 1920, height = 16 }
       -- Works but is too thin and does not fit stalonetray..
       -- , position = Top C 100
       -- interval are tenth of seconds, e.g:
       --  10 -> second
       --  600 -> minute
       --  18000 -> half an hour
       --  36000 -> hour
       , commands = [ Run DynNetwork [ "-L", "8", "-H", "32"
                                     , "-l", "#C9A34E", "-n", "#429942"
                                     , "-h", "#A36666"
                                     , "-t", "<dev>: <rx> / <tx>"
                                     ] 300
                    -- http://weather.noaa.gov/: This Service is no longer available
                    -- , Run Weather "LGAV" [ "-t", "<skyCondition> <tempC>C"
                    --                      , "-L", "10", "-H", "30"
                    --                      , "-n","#CEFFAC", "-h", "#FFB6B0"
                    --                      ,"-l","#96CBFE"
                    --                      ] 1200
                    , Run Cpu [ "-L", "3", "-H", "50"
                              , "--normal", "#429942"
                              , "--high", "#A36666"
                              ] 300
                    , Run Memory [ "-t", "Mem: <usedratio>%" ] 100
                    , Run Date "%a %b %_d %Y %H:%M" "date" 600
                    , Run Battery [ "-t", "Batt[<acstatus>]: <left>%"
                                  , "--Low"      , "10"        -- units: %
                                  , "--High"     , "80"        -- units: %
                                  , "--low"      , "darkred"
                                  , "--normal"   , "darkorange"
                                  , "--high"     , "darkgreen"
                                  , "--" -- battery specific options
                                  -- see /sys/class/power_supply/BAT0/
                                  -- , "-c", "energy_full"
                                  -- AC "on" status
                                  , "-O" , "AC"
                                  , "-i" , "FULL"
                                  -- AC "off" status
                                  , "-o" , "DC"
                                  -- , "-O" , "<fc=green>AC</fc>"
                                  ] 600
                    , Run Kbd [ ("us", "us")
                              , ("gr", "gr")
                              ]
                    -- FIXME: What about core{1.3}??
                    , Run CoreTemp [ "--template" , "Temp: <core0>°C"
                                   , "--Low"      , "70"        -- units: °C
                                   , "--High"     , "80"        -- units: °C
                                   , "--low"      , "darkgreen"
                                   , "--normal"   , "darkorange"
                                   , "--high"     , "darkred"
                                   ] 300
                    -- Debian xmobar is not compile with wireless suport
                    -- Once they do use %wlan0wi% in final template
                    -- , Run Wireless [] 100
                    -- Debian xmonad is not compiled with alsa support
                    -- Once they do use %default:Master% in final template
                    -- , Run Volume "default" "Master" [] 10
                    , Run StdinReader
                    ]
       , sepChar = "%"
       , alignSep = "}{"
       , template = " %StdinReader% }{ %battery% <fc=#429942>|</fc> %cpu% <fc=#429942>|</fc> %coretemp% <fc=#429942>|</fc> %memory% <fc=#429942>|</fc> %dynnetwork% <fc=#429942>|</fc> %kbd% <fc=#429942>|</fc> %date% "
       }

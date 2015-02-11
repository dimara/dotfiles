Config { font = "-*-terminus-*-*-*-*-12-*-*-*-*-*-*-u"
       , bgColor = "#000000"
       , fgColor = "#C9A34E"
       , border = NoBorder
       , borderColor = "#000000"
       , position = Top
       , commands = [ Run Network "eth0" [ "-L", "8", "-H", "32"
                                         , "-l", "#C9A34E", "-n", "#429942"
                                         , "-h", "#A36666"
                                         , "-t", "<dev>: <rx> / <tx>"
                                         ] 10
                    , Run Weather "LGAV" [ "-t", "<skyCondition> <tempC>C"
                                         , "-L", "10", "-H", "30"
                                         , "-n","#CEFFAC", "-h", "#FFB6B0"
                                         ,"-l","#96CBFE"
                                         ] 360
                    , Run Cpu [ "-L", "3", "-H", "50"
                              , "--normal", "#429942"
                              , "--high", "#A36666"
                              ] 10
                    , Run Memory [ "-t", "Mem: <usedratio>%" ] 10
                    , Run Date "%a %b %_d %Y %H:%M:%S" "date" 10
                    , Run Battery [ "-t", "Batt(<acstatus>): <left>% / <timeleft>"
                                  , "--Low"      , "10"        -- units: %
                                  , "--High"     , "80"        -- units: %
                                  , "--low"      , "darkred"
                                  , "--normal"   , "darkorange"
                                  , "--high"     , "darkgreen"
                                  , "--" -- battery specific options
                                  -- see /sys/class/power_supply/BAT0/
                                  , "-c", "energy_full"
                                  -- discharging status
                                  , "-o" , "DC"
                                  -- AC "on" status
                                  -- , "-O" , "<fc=green>AC</fc>"
                                  , "-O" , "AC"
                                  ] 300
                    , Run Kbd [ ("us", "us")
                              , ("gr", "gr")
                              ]
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
       , template = " %StdinReader% }{ %battery% <fc=#429942>|</fc> %cpu% <fc=#429942>|</fc> %memory% <fc=#429942>|</fc> %eth0% <fc=#429942>|</fc> %kbd% <fc=#429942>|</fc> %date% <fc=#429942>|</fc> %LGAV% "
       }

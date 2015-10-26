{-# OPTIONS_GHC -Wall -fno-warn-unused-binds #-}
import XMonad
import XMonad.Hooks.DynamicLog
import XMonad.Hooks.FadeInactive
import XMonad.Hooks.FloatNext
import XMonad.Hooks.ManageDocks
import XMonad.Hooks.ManageHelpers
import XMonad.Hooks.Place

-- layouts
import XMonad.Layout.IM
import XMonad.Layout.Grid
import XMonad.Layout.Named
import XMonad.Layout.NoBorders
import XMonad.Layout.PerWorkspace
import XMonad.Layout.Reflect
import XMonad.Layout.ResizableTile
import XMonad.Layout.SimplestFloat
import XMonad.Layout.ThreeColumns

import XMonad.Actions.CycleWS

import XMonad.Util.Run(spawnPipe)
import XMonad.Util.EZConfig(additionalKeys)

import Graphics.X11.ExtraTypes.XF86

import Data.List
import System.IO
import qualified Data.Monoid
import qualified XMonad.StackSet as S

myTerminal, myBrowser :: [Char]
myTerminal = "urxvt"
myBrowser = "google-chrome-stable"

altMask, winMask, myModMask :: KeyMask
altMask = mod1Mask
winMask = mod4Mask
myModMask = mod1Mask

myBorderWidth :: Dimension
myBorderWidth = 1

-- -------------------------------------------------------------------
-- Status bars and logging
myLogHook :: Handle -> X ()
myLogHook xmproc = do
  fadeInactiveLogHook 0.9
  dynamicLogWithPP $ xmobarPP
    { ppOutput = hPutStrLn xmproc
    , ppTitle  = xmobarColor "green" "" . shorten 50
    , ppUrgent = xmobarColor "yellow" "red" . xmobarStrip
    }

-- -------------------------------------------------------------------
-- Workspaces
myWorkSpaces :: [String]
myWorkSpaces =
  [ "1:mail", "2:web", "3:talk", "4:code", "5:media"
  , "6:vbox", "7:code", "8:code", "9:code", "0:bash"
  ]


----------------------------------------------------------------------
-- Window rules
-- Execute arbitrary actions and WindowSet manipulations when managing
-- a new window. You can use this to, for example, always float a
-- particular program, or have a client always appear on a particular
-- workspace.
--
-- To find the property name associated with a program, use
-- > xprop | grep WM_CLASS
-- and click on the client you're interested in.
--
-- To match on the WM_NAME, you can use 'title' in the same way that
-- 'className' and 'resource' are used below.
myManageHook :: Query (Data.Monoid.Endo WindowSet)
myManageHook = composeAll
  [ resource  =? "desktop_window"        --> doIgnore
  , resource  =? "Dialog"                --> doFloat
  , className =? "Skype"                 --> doShift "3:talk"
  , className =? "Pidgin"                --> doShift "3:talk"
  , className =? "Galculator"            --> doFloat
  , className =? "MPlayer"               --> doShift "5:media"
  , className =? "Vlc"                   --> doShift "5:media"
  , className =? "Eog"                   --> doShift "5:media"
  , className =? "VirtualBox"            --> doShift "6:vbox"
  , className =? "rdesktop"              --> doShift "6:vbox"
  , className =? "remmina"               --> doShift "6:vbox"
  -- , isFullscreen --> (doF S.focusDown <+> doFullFloat)
  , manageDocks
  ]

-- -------------------------------------------------------------------
-- Layouts
myLayoutHook = avoidStruts
  $ onWorkspace "1:mail" common
  $ onWorkspace "2:web" common
  $ onWorkspace "3:talk" im
  $ onWorkspace "6:vbox" (full ||| tall)
  $ standardLayouts
    where
  standardLayouts = tall ||| grid ||| full ||| mirror ||| float ||| three

  --Layouts
  tall = named "Tall" $ smartBorders (ResizableTall 1 (3/100) (1/2) [])
  three = named "3Col" $ smartBorders (ThreeCol 1 (3/100) (1/3))
  full = named "Full" $ noBorders Full
  grid = named "Grid" $ smartBorders Grid
  float = named "Float" $ simplestFloat
  mirror = named "Mirror" $ Mirror tall

  --Im Layout
  im = named "IM"
    $ withIM (0.18) pidginRoster $ reflectHoriz
    $ withIM (0.22) skypeRoster (grid ||| full)
      where
    pidginRoster = (And (ClassName "Pidgin") (Role "buddy_list"))
    skypeRoster = (And (ClassName "Skype") (Title "dimitris.aragiorgis - Skype™"))

  --Web Layout
  common = full ||| mirror ||| tall

-- -------------------------------------------------------------------
-- Additional Keys
myKeys :: [((KeyMask, KeySym), X ())]
myKeys =
  [ ((0, xF86XK_AudioRaiseVolume), spawn "amixer -q set Master 5%+ unmute")
  , ((0, xF86XK_AudioLowerVolume), spawn "amixer -q set Master 5%- unmute")
  , ((0, xF86XK_AudioMute), spawn "amixer -q set Master toggle")
  , ((0, xF86XK_MonBrightnessUp), spawn "xbacklight +20")
  , ((0, xF86XK_MonBrightnessDown), spawn "xbacklight -20")
  , ((0, xK_Print), spawn "scrot -q 1 $HOME/Pictures/Screenshots/%Y-%m-%d-%H:%M:%S.png")
  , ((altMask .|. shiftMask, xK_BackSpace), spawn "xscreensaver-command -lock")
  , ((altMask, xK_p), spawn "dmenu_run -fn BitstreamVeraSansMono:size=10:dpi=168:antialias=true")
  , ((altMask, xK_Return), spawn myTerminal)
  , ((altMask .|. shiftMask, xK_Return), windows S.swapMaster)
  , ((altMask, xK_i), spawn myBrowser)
  , ((altMask, xK_w), kill)
  , ((altMask, xK_t), withFocused $ windows . S.sink)
  , ((altMask, xK_f), withFocused $ float)
  , ((altMask, xK_m), withFocused $ mouseMoveWindow)
  , ((altMask, xK_r), withFocused $ mouseResizeWindow)
  , ((altMask, xK_grave), nextScreen)
  , ((altMask, xK_Escape), swapPrevScreen)
  ] ++

  -- mod-[1..9], Switch to workspace N
  -- mod-shift-[1..9], Move client to workspace N
  [ ((m .|. altMask, k), windows $ f i)
      | (i, k) <- zip myWorkSpaces ([xK_1 .. xK_9] ++ [xK_0])
      , (f, m) <- [(S.greedyView, 0), (S.shift, shiftMask)]
  ] ++

  -- win-{1,2,3}, Switch to physical/Xinerama screens 1, 2, or 3
  -- win-shift-{1,2,3}, Move client to screen 1, 2, or 3
  [ ((m .|. winMask, key), screenWorkspace sc >>= flip whenJust (windows . f))
      | (key, sc) <- zip [xK_1, xK_2, xK_3] [0..]
      , (f, m) <- [(S.view, 0), (S.shift, shiftMask)]
  ]


main :: IO ()
main = do
  xmproc <- spawnPipe "xmobar ~/.xmonad/xmobar.hs"
  xmonad $ defaultConfig
    { terminal    = myTerminal
    , workspaces  = myWorkSpaces
    , modMask     = myModMask
    , borderWidth = myBorderWidth
    , manageHook  = myManageHook <+> manageHook defaultConfig
    , layoutHook  = myLayoutHook
    , logHook     = myLogHook xmproc
    } `additionalKeys` myKeys

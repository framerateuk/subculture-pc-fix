# How it works

Notes on the English retail release of Sub Culture (Criterion Studios / Ubi Soft, disc label
`SC_ENGLISH`, mastered 9 October 1997, version 1.14). Addresses are virtual addresses in
`sc3dfx.exe` unless stated.

## The disc

One MODE1 data track (186,006 sectors) and eleven audio tracks (2-12). The game has no real
installer: it runs from the disc's files, so `build.py` copies the data track's ISO 9660 file
system, leaving out `directx\`, `install\`, `3dfx\` (the Glide driver installer), `powervr\`,
`verite\`, the autorun files, the DirectX setup DLLs and the PowerVR / Rendition Verite builds
(`scpvr.*`, `scverite.*`; no wrapper runs them today). The five original exes go to `_spare\`.

The exes read nothing from the registry (they don't import ADVAPI32). Saves and settings go in the
working directory.

## CD audio

All five exes play music through MCI (`mciSendCommandA` / `mciSendStringA`) and set its volume
through the `aux*` API. The music module (0x43b0e0-0x43b7a0):

- open: `MCI_OPEN` of "cdaudio", then `set cdaudio time format tmsf`;
- play: `MCI_PLAY` with `MCI_FROM|MCI_TO` from track N to track N+1, i.e. exactly one track;
- loop: a 10-second `timeSetEvent` timer asks `MCI_STATUS_MODE` and replays the track when it
  reports `MCI_MODE_STOP`;
- pause/resume: `pause cdaudio`, remember `MCI_STATUS_POSITION`, later play from there;
- volume: the aux device whose `wTechnology` is `AUXCAPS_CDAUDIO`, through `auxSetVolume`.

ogg-winmm is a replacement `winmm.dll` that answers all of that by playing `Music\TrackNN.ogg`,
including a fake CD-audio aux device, so the in-game music slider works. "Play 12 to 13" on the
last track is clamped to the end of track 12. Wine treats `winmm` as a builtin, so the launch
script sets `WINEDLLOVERRIDES=winmm=n,b`. Each track is ripped from its INDEX 01 to the next
track's start, so lengths match the disc's table of contents. `data\CD.CFG` maps levels to tracks.

## The disc check and file lookup

There's no `GetDriveTypeA` and no volume label check. Two separate mechanisms:

1. **Disc presence** (sc3dfx.exe 0x45ab70, sc.exe 0x42d900, scd3d.exe 0x404a90; scpvr.exe
   0x439a30, scverite.exe 0x415cd0): for drive letters B to Z, accept the first where
   `GetDiskFreeSpaceA` reports 0 free clusters, `X:\sc.exe` opens for reading, and `X:\sc.exe`
   fails to open for writing, i.e. a read-only disc holding the game. Callers do
   `if (!found) show gametex\cdcheck.bmp and loop until a disc appears`.
2. **File lookup** (around 0x4337xx): every file is tried relative to the working directory first;
   only if that fails is it tried as `X:\dir\file` with X from `CDDRV.CFG`, skipped when the
   letter is `-`. The disc ships `C`; `build.py` writes `-`.

Under Wine a folder presented as a CD-ROM drive reports the host file system's free space, never
0, so test 1 can't pass on the Steam Deck. A disc image mounted on Windows reports 0 free and
passes. `patch_exes.py` ("nocd") replaces the function's first 6 bytes with `mov eax,1 ; ret`; it
is located by its prologue, identical in all five exes:

| exe | function VA | file offset | callers |
|---|---|---|---|
| sc3dfx.exe | 0x45ab70 | 0x59f70 | 2 |
| sc.exe | 0x42d900 | 0x2cd00 | 2 |
| scd3d.exe | 0x404a90 | 0x3e90 | 4 |
| scpvr.exe | 0x439a30 | 0x38e30 | 4 (not patched) |
| scverite.exe | 0x415cd0 | 0x150d0 | 2 (not patched) |

The "CD Error !" message boxes elsewhere in the exe are file load failures ("Could not load
mission object", "Clump not loaded..."), not disc checks.

## Mouse pointer

The game creates a plain 640x480 window whose window class has the standard arrow cursor. It
hides the pointer with `SetCursor(NULL)`, reads the mouse as `WM_MOUSEMOVE` deltas and warps the
real pointer back to the screen centre after each move (`SetCursorPos`, 0x41b248); menus draw
their own pointer. Each mouse move makes `DefWindowProc` restore the class arrow. On a real Voodoo
card that was invisible (the 3dfx card owned the monitor), but under dgVoodoo on Windows it shows
as an arrow jittering near the middle of the screen. "nocursor" changes one byte at the class
cursor store (sc3dfx.exe 0x431d0a, sc.exe 0x46092a, scd3d.exe 0x47666a): `mov [esp+0x38],eax`
becomes `mov [esp+0x38],edi`, edi being the NULL passed to `LoadCursorA`, so the class has no
cursor and `SetCursor(NULL)` sticks.

## Graphics

`sc3dfx.exe` imports `glide2x.dll` directly (Glide 2.x, needs 2.42 or later) and no DirectDraw,
and `SMACKW32.DLL` imports only WINMM, GDI, USER and KERNEL, so the menus and videos are drawn
through Glide too. dgVoodoo2's `glide2x.dll` loads from the game folder with no override (Wine has
no builtin). `scd3d.exe` and `sc.exe` use DirectDraw (and Direct3D through `QueryInterface`), so
they need `ddraw=n,b;d3dimm=n,b`; `RENDERER=wined3d` drops those to Wine's own.

Version 2.79.3 is needed under Wine: 2.80 and later fail to initialise DirectDraw there (Wine bug
58731). `dgVoodoo.conf`: `[Glide] VideoCard = voodoo_graphics`, `OnboardRAM = 4`,
`NumberOfTMUs = 1` (the card the game was made for), `Resolution = 2x` (1280x960), watermark and
splash off; `FPSLimit = 60`, forced vsync, `ScalingMode = stretched_ar` (4:3 with bars).

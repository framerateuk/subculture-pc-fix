# Sub Culture (PC, 1997) on modern PCs and the Steam Deck

## Why this exists

Sub Culture had an amazing atmosphere that other underwater games have failed to match. The
trading system was excellent and the combat was fun, and I haven't played another game like it.
It isn't sold anywhere any more. Getting your own copy running today means fighting a CD check
that modern systems can't pass, CD-audio music, a 3dfx Glide renderer and a mouse pointer stuck
on screen. This kit sorts all of that out, so it can be played again.

## What this does

Turns **your own** English Sub Culture CD into a folder that runs on the Steam Deck (Proton) or on
Windows 10/11, with no installer and no registry entries:

- **Copied straight from the CD**: the game runs from its disc files, so nothing is installed.
- **CD soundtrack** from OGG files ripped from your disc. The in-game music volume works.
- **3dfx Glide** through dgVoodoo2 (on the Deck: Vulkan via DXVK), as a Voodoo Graphics card
  rendering at 1280x960, 4:3, capped at 60 fps. The Direct3D and software builds are there too.
- **The CD check**: it looks for a full, read-only drive holding the game, which a modern PC (and
  Proton on the Deck) can't offer from a disc image, so the three exes get a 6-byte change that
  skips it. On Windows you can keep it instead (below).
- **No stray mouse pointer**: a 1-byte change stops the Windows arrow jittering in the middle of
  the screen (the game draws its own pointer in the menus).

**No game files are in this repository.** Everything from the game comes from your disc when you
run `build.py`.

## What you need

| | |
|---|---|
| The game | The **English Sub Culture CD** (Criterion / Ubi Soft, 1997, version 1.14, volume label `SC_ENGLISH`) as `.cue` + `.bin` or CloneCD `.ccd` + `.img`, with its audio tracks. `build.py` checks the exes and stops on another edition. |
| Python | 3.8 or newer (python.org on Windows; already on macOS/Linux). |
| An OGG encoder | `oggenc` (vorbis-tools; Windows builds at rarewares.org) or `ffmpeg`, on the PATH. |
| dgVoodoo2 **2.79.3** | by Dege: [GitHub release v2.79.3](https://github.com/dege-diosg/dgVoodoo2/releases/tag/v2.79.3). Use 2.79.3: newer versions don't start under Wine/Proton. Keep the zip as downloaded. |
| ogg-winmm | by AyuanX: [GitHub releases](https://github.com/ayuanx/ogg-winmm/releases) (tested with v2025.01.16). Keep the zip as downloaded. |

## Build

```
python3 build.py SC_ENGLISH.cue --dgvoodoo dgVoodoo2_79_3.zip --ogg-winmm ogg-winmm_binary.zip
```

creates `SubCulture/` with `game/` and `subculture_launch.sh` (for the Steam Deck). It takes under
a minute. The same `game/` folder runs on Windows.

For Windows only, add `--windows` (no launch script). Then the CD check:

- **default**: `sc3dfx.exe`, `scd3d.exe` and `sc.exe` get the 6-byte change, and the game runs from
  the folder with nothing mounted.
- **`--keep-cd-check`**: the check stays in the exes (only the 1-byte cursor change is made), and
  `build.py` writes `SubCulture-disc.iso` (your CD's data track). Double-click it to mount it
  before playing. Not possible on the Deck.

The disc's original exes, including the PowerVR and Rendition Verite builds, are kept unchanged in
`game/_spare/`. `--out DIR` puts the result somewhere else.

## Play on the Steam Deck

1. Copy `SubCulture/` to the Deck, for example to `/home/deck/Games/SubCulture/`.
2. Desktop Mode: Steam > Add a Non-Steam Game > Browse > `.../SubCulture/game/sc3dfx.exe`.
   Rename the shortcut "Sub Culture".
3. Properties > Compatibility: force **Proton 9.0**. Pin it rather than floating on Experimental.
4. Properties > Launch Options:
   ```
   /home/deck/Games/SubCulture/subculture_launch.sh %command%
   ```
   Don't leave out `%command%`: without it the game still starts, but with no music.
5. Launch: Smacker intro, then the menu, with music from the first screen. `launch.log` beside the
   script shows what it did.
6. Steam Input: start from the "Gamepad with Mouse Trackpad" template. The game also reads a
   joystick; select it in the in-game controls if you prefer.

## Play on Windows

Run `game/sc3dfx.exe` (with `--keep-cd-check`, mount `SubCulture-disc.iso` first). If it shows a
black screen, try `scd3d.exe`; both use the same data. A shortcut must start in the `game` folder.

## In the game

- `sc3dfx.exe` (3dfx Glide) looks best. `scd3d.exe` is Direct3D 5, `sc.exe` the software renderer.
- Saves and settings (`save.cfg`, `control.cfg`) are written inside `game/`, so the folder is
  portable.

## Tuning

- `game/dgVoodoo.conf`: `[Glide] Resolution` (`unforced` = the original 640x480, `2x`, `3x`,
  `max`), `[GeneralExt] FPSLimit`, `[General] ScalingMode`. On Windows the four dgVoodoo files can
  be swapped for the current dgVoodoo2 release (2.79.3 is only needed under Wine/Proton).
- Music level: the in-game slider, or `CDDAVolume` in `game/winmm.ini` (0-100).
- Which track plays where: `game/data/CD.CFG`.
- Deck renderer for `scd3d.exe` / `sc.exe`: put `RENDERER=wined3d` (plain Wine DirectDraw/Direct3D)
  before the script path in the launch options. Default: dgVoodoo for everything.

## Troubleshooting

- *"Please insert the CD" screen*: you're running an unpatched exe (from `_spare/`, a fresh copy
  of the disc, or a `--keep-cd-check` build with nothing mounted). `python3 patch_exes.py EXE`
  patches it.
- *No music*: `launch.log` must exist and show `WINEDLLOVERRIDES=winmm=n,b;...` (if there's no log,
  the launch option is missing `%command%`), and `game/Music/Track02.ogg` must exist.
- *Music stops for a few seconds at the end of a track*: the game checks every 10 seconds whether
  to start the track again; that's how it was.
- *Black screen with `sc3dfx.exe`*: try `Resolution = unforced`, then `scd3d.exe` as the target.
- *"CD Error !" message boxes*: a file failed to load, usually because the game wasn't started in
  the `game` folder.
- *No sound in the videos*: check `WAVEVolume` in `game/winmm.ini`.

## What's in this repository

| File | What |
|---|---|
| `build.py` | Builds the folder: copies the CD's files, patches the exes, rips the soundtrack, adds the wrappers and settings. Python standard library only. |
| `patch_exes.py` | The two exe patches (disc check, mouse pointer); also runs on its own. |
| `disc.py` | Reads the CD image: `.cue`/`.bin` or `.ccd`/`.img`, ISO 9660 and audio tracks. |
| `config/dgVoodoo.conf` | dgVoodoo2 settings. |
| `steamdeck/subculture_launch.sh` | Proton launch wrapper: DLL overrides. |
| `docs/TECHNICAL.md` | How each part works. |

## Credits

- **Criterion Studios** made Sub Culture; **Ubi Soft** published it. Please own the game: this kit
  needs your disc.
- **Dege**: dgVoodoo2. **AyuanX**: ogg-winmm.

## License

The scripts and docs in this repository: MIT (see `LICENSE`). The license covers only this
repository's own files, not the game, dgVoodoo2 or ogg-winmm.

Not affiliated with or endorsed by the game's rights holders.

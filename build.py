#!/usr/bin/env python3
"""Build a ready-to-run Sub Culture folder for modern PCs from your own CD.

Usage:
  python3 build.py DISC.cue|DISC.ccd --dgvoodoo DGVOODOO.zip --ogg-winmm OGG-WINMM.zip [--out DIR]
                   [--windows [--keep-cd-check]]

  DISC          your English Sub Culture CD (1997, v1.14, volume label SC_ENGLISH) as .cue + .bin
                or .ccd + .img
  --dgvoodoo    dgVoodoo2 2.79.3 zip (or its unpacked folder)
  --ogg-winmm   ogg-winmm release zip (or folder)
  --out         where to create SubCulture/ (default: this folder)
  --windows     a folder for Windows only: the same game/ folder, without the Steam Deck launch script
  --keep-cd-check  with --windows: leave the game's disc check in the exes and write
                SubCulture-disc.iso (your CD's data track) to mount before playing

Needs Python 3.8+ and an Ogg Vorbis encoder on the PATH: oggenc (vorbis-tools) or ffmpeg.
Nothing from the game is in this repository: every game file comes from your disc.
"""
import argparse, hashlib, os, shutil, struct, subprocess, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import disc, patch_exes

EXES = {   # exe: (MD5 on the English v1.14 CD, MD5 after nocd + nocursor)
    "sc3dfx.exe": ("80f4ca45c793664d1c2d350703910056", "0a7555af6e2474399f4a0193a8a09d4c"),
    "scd3d.exe": ("19396c9505ba22a823a0ef6e1db05304", "f45d3f2dbc53355463a7fc65d5c351be"),
    "sc.exe": ("da47b9fb18d2af7f5e59cb60b3daff98", "589f0eba187537121f62ccbcb5d90204"),
}
SPARE = ["sc.exe", "sc3dfx.exe", "scd3d.exe", "scpvr.exe", "scverite.exe"]   # the disc's exes, unchanged
# Left on the disc: installers (DirectX 5, the 3dfx Glide driver, the game's own), autorun, and the
# PowerVR and Rendition Verite builds, which no wrapper can run today.
SKIP_DIRS = {"directx", "install", "3dfx", "powervr", "verite"}
SKIP_FILES = {"dsetup.dll", "dsetup16.dll", "dsetup32.dll", "autorun.exe", "autorun.inf"}
SKIP_PREFIXES = ("scpvr.", "scverite.")


def md5(data): return hashlib.md5(data).hexdigest()


def skipped(path):
    parts = path.lower().split("/")
    if any(p in SKIP_DIRS for p in parts[:-1]) or parts[-1] in SKIP_DIRS: return True
    return parts[-1] in SKIP_FILES or parts[-1].startswith(SKIP_PREFIXES)


def encoder():
    if shutil.which("oggenc"): return lambda wav, ogg: ["oggenc", "-Q", "-q", "7", wav, "-o", ogg]
    if shutil.which("ffmpeg"):
        return lambda wav, ogg: ["ffmpeg", "-loglevel", "error", "-y", "-i", wav, "-c:a", "libvorbis", "-q:a", "7", ogg]
    sys.exit("needs oggenc (vorbis-tools) or ffmpeg on the PATH to encode the soundtrack")


def rip(tracks, music):
    enc = encoder(); os.makedirs(music, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for t in tracks:
            if t.kind != "AUDIO": continue
            data = disc.audio(t)          # INDEX 01 to the next track's start: lengths match the disc's TOC
            wav = os.path.join(tmp, f"track{t.n:02d}.wav")
            with open(wav, "wb") as o:
                o.write(b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVEfmt " +
                        struct.pack("<IHHIIHH", 16, 1, 2, 44100, 176400, 4, 16) + b"data" +
                        struct.pack("<I", len(data)) + data)
            subprocess.run(enc(wav, os.path.join(music, f"Track{t.n:02d}.ogg")), check=True); os.remove(wav)
            print(f"  Music/Track{t.n:02d}.ogg  {len(data) / 2352 / 75:6.1f} s")


def take(src, member):
    """Bytes of the file whose path ends with `member` (case-insensitive) in a zip or folder."""
    want = member.lower()
    if os.path.isdir(src):
        for d, _, fs in os.walk(src):
            for f in fs:
                p = os.path.join(d, f)
                if os.path.relpath(p, src).replace(os.sep, "/").lower().endswith(want): return open(p, "rb").read()
    else:
        with zipfile.ZipFile(src) as z:
            for name in z.namelist():
                if name.lower().endswith(want): return z.read(name)
    sys.exit(f"{member} not found in {src}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("disc"); ap.add_argument("--dgvoodoo", required=True); ap.add_argument("--ogg-winmm", required=True)
    ap.add_argument("--out", default=HERE); ap.add_argument("--windows", action="store_true")
    ap.add_argument("--keep-cd-check", action="store_true")
    a = ap.parse_args()
    if a.keep_cd_check and not a.windows:
        sys.exit("--keep-cd-check goes with --windows (under Proton the disc check can't be passed, see README)")

    tracks = disc.tracks(a.disc)
    data = [t for t in tracks if t.kind != "AUDIO"]
    if not data: sys.exit("no data track in " + a.disc)
    dt = disc.DataTrack(data[0])
    if dt.label() != "SC_ENGLISH": print(f"warning: volume label is {dt.label()!r}, this kit was made for SC_ENGLISH")
    entries = {p.lower(): (p, is_dir, l, s) for p, is_dir, l, s in dt.walk()}
    for exe, (want, _) in EXES.items():
        if exe not in entries: sys.exit(f"no {exe} on this CD: it isn't the Sub Culture disc the kit was made for")
        got = md5(dt.read_file(*entries[exe][2:]))
        if got != want:
            sys.exit(f"this CD's {exe} is not the English v1.14 one the kit was made for (MD5 {got}); "
                     "nothing else is supported yet")

    pkg = os.path.join(os.path.abspath(a.out), "SubCulture"); game = os.path.join(pkg, "game")
    if os.path.exists(pkg): sys.exit(f"{pkg} already exists: move or delete it first")

    print("1/5 game files from the CD")
    for p, is_dir, l, s in entries.values():
        if is_dir or skipped(p): continue
        dt.copy_file(l, s, os.path.join(game, *p.split("/")))
    for exe in SPARE:
        p, _, l, s = entries[exe]
        dt.copy_file(l, s, os.path.join(game, "_spare", p))
    with open(os.path.join(game, "CDDRV.CFG"), "wb") as f:
        f.write(b"-\r\n")     # no CD drive letter: never look for files outside the game folder

    print("2/5 exe patches" + (" (disc check kept)" if a.keep_cd_check else ""))
    names = ("nocursor",) if a.keep_cd_check else ("nocd", "nocursor")
    for exe, (_, patched) in EXES.items():
        path = os.path.join(game, entries[exe][0])
        out = patch_exes.patch(open(path, "rb").read(), names, exe)
        if not a.keep_cd_check and md5(out) != patched: sys.exit(f"patching gave an unexpected {exe}")
        open(path, "wb").write(out)
    if a.keep_cd_check:
        dt.write_iso(os.path.join(pkg, "SubCulture-disc.iso"))

    print("3/5 soundtrack")
    rip(tracks, os.path.join(game, "Music"))

    print("4/5 wrappers and settings")
    for member, name in [("MS/x86/DDraw.dll", "ddraw.dll"), ("MS/x86/D3DImm.dll", "d3dimm.dll"),
                         ("3Dfx/x86/Glide2x.dll", "glide2x.dll")]:
        open(os.path.join(game, name), "wb").write(take(a.dgvoodoo, member))
    for name in ("winmm.dll", "winmm.ini"):
        open(os.path.join(game, name), "wb").write(take(a.ogg_winmm, name))
    shutil.copyfile(os.path.join(HERE, "config", "dgVoodoo.conf"), os.path.join(game, "dgVoodoo.conf"))

    print("5/5 Steam Deck launch script" if not a.windows else "5/5 done")
    if not a.windows:
        launch = os.path.join(pkg, "subculture_launch.sh")
        shutil.copyfile(os.path.join(HERE, "steamdeck", "subculture_launch.sh"), launch); os.chmod(launch, 0o755)
    print(f"\ndone: {pkg}  (see README.md)")


if __name__ == "__main__":
    main()

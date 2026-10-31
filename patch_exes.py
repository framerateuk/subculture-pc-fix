#!/usr/bin/env python3
"""Patch Sub Culture's exes (sc.exe, sc3dfx.exe, scd3d.exe; English retail v1.14, Oct 1997) in place.

Usage:  patch_exes.py [--keep-cd-check] EXE [EXE ...]
        each patch must match exactly once (or already be applied), or the file is left unchanged

1. nocd (6 bytes). The disc check is a function (sc3dfx.exe 0x45ab70, sc.exe 0x42d900,
   scd3d.exe 0x404a90; also scpvr.exe 0x439a30, scverite.exe 0x415cd0) that scans drives
   B:..Z: for one where GetDiskFreeSpaceA reports 0 free clusters, X:\\sc.exe opens for
   reading and fails to open for writing, i.e. a read-only disc holding the game. It returns
   1 if found. Every caller does `if (!found) show cdcheck.bmp and loop until a disc appears`.
   The patch makes the function start with `mov eax,1 ; ret`. Nothing else depends on it:
   assets load from the working directory first and only fall back to the CDDRV.CFG letter.

2. nocursor (1 byte). The game window's class cursor is LoadCursorA(NULL, IDC_ARROW)
   (sc3dfx.exe 0x431d0a, sc.exe 0x46092a, scd3d.exe 0x47666a). The game hides the pointer
   with SetCursor(NULL) and reads the mouse as deltas, warping it back to the screen centre,
   but every mouse move makes DefWindowProc restore the class arrow. On a real Voodoo the
   desktop wasn't on screen; under dgVoodoo the arrow shows, jittering near the middle.
   The patch stores the zero register instead of the LoadCursorA result in WNDCLASS.hCursor
   (`mov [esp+0x38],eax` -> `mov [esp+0x38],edi`; edi is the NULL hInstance passed to
   LoadCursorA), so the window has no class cursor and SetCursor(NULL) sticks.
"""
import re, sys

PATCHES = [
    # name, pattern (group 1 = bytes to replace), replacement, already-applied pattern
    ("nocd",
     re.compile(rb"(\x81\xec\x18\x01\x00\x00)\x53\x56\x57\x8b\x35....\xbf\x01\x00\x00\x00\x33\xdb\x8d\x47\x41", re.S),
     b"\xb8\x01\x00\x00\x00\xc3",
     re.compile(rb"\xb8\x01\x00\x00\x00\xc3\x53\x56\x57\x8b\x35....\xbf\x01\x00\x00\x00\x33\xdb\x8d\x47\x41", re.S)),
    ("nocursor",
     re.compile(rb"\x68\x00\x7f\x00\x00\x57\xff\x15....\x8b\x2d....(\x89\x44\x24\x38)", re.S),
     b"\x89\x7c\x24\x38",
     re.compile(rb"\x68\x00\x7f\x00\x00\x57\xff\x15....\x8b\x2d....\x89\x7c\x24\x38", re.S)),
]


def patch(data, names=("nocd", "nocursor"), label="exe"):
    """Returns the patched bytes; exits if a patch doesn't match exactly once."""
    d = bytearray(data)
    for name, pat, new, done in PATCHES:
        if name not in names: continue
        if len(list(done.finditer(d))) == 1:
            print(f"  {label}: {name} already applied"); continue
        hits = list(pat.finditer(d))
        if len(hits) != 1:
            sys.exit(f"{label}: {name}: expected one match, found {len(hits)}; file left unchanged")
        o = hits[0].start(1)
        d[o:o + len(new)] = new
        print(f"  {label}: {name} at file offset {o:#x}")
    return bytes(d)


if __name__ == "__main__":
    args = sys.argv[1:]
    names = ("nocursor",) if "--keep-cd-check" in args else ("nocd", "nocursor")
    for path in [p for p in args if p != "--keep-cd-check"]:
        out = patch(open(path, "rb").read(), names, path)
        open(path, "wb").write(out)

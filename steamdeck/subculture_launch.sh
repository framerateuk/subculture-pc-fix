#!/bin/bash
# Sub Culture (PC, 1997) Steam Deck / Proton launch wrapper.
#
# Keep it beside game/ (build.py puts it there). With the folder at /home/deck/Games/SubCulture:
#   Shortcut target: /home/deck/Games/SubCulture/game/sc3dfx.exe, Start In: .../game/
#   Steam > Sub Culture > Properties > Launch Options:
#     /home/deck/Games/SubCulture/subculture_launch.sh %command%
#
# The shortcut target picks the renderer build (all in game/, all with the disc check patched out):
#   sc3dfx.exe  3Dfx Glide   -> dgVoodoo2 glide2x.dll   (recommended)
#   scd3d.exe   Direct3D 5   -> dgVoodoo2 ddraw/d3dimm
#   sc.exe      software     -> dgVoodoo2 ddraw
#
# Every launch sets DLL overrides so Wine loads the wrappers sitting beside the exe:
#   winmm.dll   ogg-winmm: CD audio from Music/TrackNN.ogg, plus the CD-audio volume control
#   ddraw.dll, d3dimm.dll   dgVoodoo2 2.79.3 (glide2x.dll has no Wine builtin, it always loads)
# No fake CD-ROM drive: the patched exes skip the disc check and every file loads from game/
# (see docs/TECHNICAL.md).
#
# RENDERER (set before the script path in Launch Options, default dgvoodoo):
#   dgvoodoo  ddraw+d3dimm+glide2x all from dgVoodoo2
#   wined3d   plain Wine ddraw/d3d for scd3d.exe / sc.exe; glide2x still dgVoodoo
#   Example:  RENDERER=wined3d /home/deck/Games/SubCulture/subculture_launch.sh %command%

set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$HERE/launch.log"
RENDERER="${RENDERER:-dgvoodoo}"
log() { echo "[$(date '+%H:%M:%S')] $*" >>"$LOG"; }
: >"$LOG"
log "args: $*"
log "RENDERER=$RENDERER  STEAM_COMPAT_DATA_PATH=${STEAM_COMPAT_DATA_PATH:-unset}"

# Proton appends its own overrides after ours.
OVR="winmm=n,b"
case "$RENDERER" in
  dgvoodoo) OVR="$OVR;ddraw=n,b;d3dimm=n,b" ;;
  wined3d)  OVR="$OVR;ddraw=b;d3dimm=b" ;;
  *)        log "unknown RENDERER '$RENDERER', using dgvoodoo"; OVR="$OVR;ddraw=n,b;d3dimm=n,b" ;;
esac
export WINEDLLOVERRIDES="${OVR}${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"
log "WINEDLLOVERRIDES=$WINEDLLOVERRIDES"

for f in winmm.dll winmm.ini glide2x.dll ddraw.dll d3dimm.dll dgVoodoo.conf Music/Track02.ogg; do
  [ -e "$HERE/game/$f" ] || log "WARNING: game/$f missing"
done

log "exec: $*"
exec "$@"

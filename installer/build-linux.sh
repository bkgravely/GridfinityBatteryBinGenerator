#!/usr/bin/env bash
# Build the MSI on Linux with msitools (wixl), as an alternative to the
# WiX Toolset build documented in build.ps1.
#
# Two wixl quirks are handled here:
#   * wixl rejects <WixVariable>, so make_wxs.py only emits those with --wix
#     (the Windows path). wixl instead finds License.rtf by filename.
#   * the WixUI bitmaps are embedded from the extension directory by filename,
#     and a <Binary> of the same id in our own source collides on the Binary
#     table's primary key. So the extension directory is copied and the two
#     bitmaps swapped for the branded ones before building.
#
# Usage:  installer/build-linux.sh [output.msi]
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(dirname "$HERE")"
VERSION="$(sed -n "s/^VERSION = '\([^']*\)'.*/\1/p" "$HERE/make_wxs.py")"
OUT="${1:-$REPO/GridfinityBatteryBinGenerator-${VERSION}-x64.msi}"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

cp -r "$REPO/GridfinityBatteryBinGenerator" "$WORK/"
rm -rf "$WORK/GridfinityBatteryBinGenerator/tests"
find "$WORK" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
cp "$HERE"/make_wxs.py "$HERE"/License.rtf "$HERE"/ProductIcon.ico \
   "$HERE"/dlgbmp.bmp "$HERE"/bannrbmp.bmp "$WORK/"

EXTSRC="$(ls -d /usr/share/wixl-*/ext | head -1)"
cp -r "$EXTSRC" "$WORK/ext"
cp "$HERE/dlgbmp.bmp" "$WORK/ext/ui/bitmaps/dlgbmp.bmp"
cp "$HERE/bannrbmp.bmp" "$WORK/ext/ui/bitmaps/bannrbmp.bmp"

cd "$WORK"
python3 make_wxs.py
wixl --extdir "$WORK/ext" --ext ui --arch x64 -o "$OUT" GridfinityBatteryBinGenerator.wxs

# Third wixl quirk: it does not implement Component/@Permanent, and says so on
# stderr rather than failing. Those two components exist to hold
# Autodesk\ApplicationPlugins open - Windows Installer deletes any directory it
# created once the last thing in it is removed, so without them uninstalling
# this add-in takes the shared plugin folder with it whenever ours is the only
# plugin there. Set the permanent bit (16) on top of the 64-bit bit (256) that
# wixl did write. The WiX Toolset path honours Permanent="yes" directly and
# needs none of this.
for component in cmpKeepAutodesk cmpKeepAppPlugins; do
  msibuild "$OUT" -q "UPDATE \`Component\` SET \`Attributes\` = 272 WHERE \`Component\` = '$component'"
done
for component in cmpKeepAutodesk cmpKeepAppPlugins; do
  msiinfo export "$OUT" Component | awk -F'\t' -v c="$component" '$1==c && $4!=272 {
      print "ERROR: " c " is not marked permanent (attributes " $4 ")"; exit 1 }'
done
cp GridfinityBatteryBinGenerator.wxs "$HERE/"
echo "Built $OUT"

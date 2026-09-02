# Rebuild the GridfinityBatteryBinGenerator MSI on Windows with the WiX Toolset.
#
# The installer shows a licence page, a progress bar and a Finish page that
# confirms the install, so the WiX UI extension is REQUIRED - without it the
# build fails on WixUI_Minimal. These four files must sit beside the .wxs at
# build time: License.rtf, ProductIcon.ico (Add/Remove Programs logo),
# dlgbmp.bmp and bannrbmp.bmp (the branded installer artwork).
#
# Generate the source with --wix so it emits the <WixVariable> elements that
# point WiX at the licence and the bitmaps; plain `python make_wxs.py` targets
# msitools/wixl instead, which rejects <WixVariable> and matches by filename.
#
# The .wxs is WiX v3 syntax. Two ways to build:
#
#   A) WiX v3 (candle/light):
#        candle -arch x64 GridfinityBatteryBinGenerator.wxs
#        light -ext WixUIExtension -dWixUILicenseRtf=License.rtf `
#              GridfinityBatteryBinGenerator.wixobj `
#              -o GridfinityBatteryBinGenerator-1.1.1-x64.msi
#
#   B) WiX v4/v5 CLI (dotnet tool install --global wix):
#        wix extension add WixToolset.UI.wixext
#        wix convert GridfinityBatteryBinGenerator.wxs   # one-time upgrade to v4 syntax
#        wix build -arch x64 -ext WixToolset.UI.wixext `
#            -d WixUILicenseRtf=License.rtf `
#            GridfinityBatteryBinGenerator.wxs `
#            -o GridfinityBatteryBinGenerator-1.1.1-x64.msi
#
#   (On Linux, msitools builds the same source: wixl --ext ui --arch x64 ...
#    which picks up License.rtf from the build folder automatically.)
#
# Regenerate the .wxs after changing add-in files (needs Python 3):
#        python make_wxs.py --wix     (Windows / WiX Toolset)
#        python make_wxs.py             (Linux / wixl - see build-linux.sh)
#
# Bump the version: edit VERSION in make_wxs.py, "version" in the add-in
# manifest, AppVersion + ComponentEntry Version in PackageContents.xml, and add
# a CHANGELOG entry - tests/test_packaging.py fails if they disagree.
# Never change UPGRADE_CODE: it is what makes upgrades replace old installs.
#
# Sign before distributing - and sign from a local path, never from inside a
# OneDrive-synced folder, or the sync engine corrupts the write and signtool
# fails with a bare error count:
#        signtool sign /fd SHA256 /td SHA256 /tr http://timestamp.digicert.com `
#                 /a GridfinityBatteryBinGenerator-1.1.1-x64.msi
#        signtool verify /pa /v GridfinityBatteryBinGenerator-1.1.1-x64.msi

$ErrorActionPreference = 'Stop'
python make_wxs.py --wix
candle -arch x64 GridfinityBatteryBinGenerator.wxs
light -ext WixUIExtension -dWixUILicenseRtf=License.rtf `
      GridfinityBatteryBinGenerator.wixobj `
      -o GridfinityBatteryBinGenerator-1.1.1-x64.msi
Write-Host "Built GridfinityBatteryBinGenerator-1.1.1-x64.msi"

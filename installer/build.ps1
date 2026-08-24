# Rebuild the GridfinityBatteryBinGenerator MSI on Windows with the WiX Toolset.
# The .wxs is WiX v3 syntax. Two ways to build:
#
#   A) WiX v3 (candle/light):
#        candle -arch x64 GridfinityBatteryBinGenerator.wxs
#        light -ext WixUtilExtension GridfinityBatteryBinGenerator.wixobj -o GridfinityBatteryBinGenerator-1.0.2-x64.msi
#
#   B) WiX v4/v5 CLI (dotnet tool install --global wix):
#        wix convert GridfinityBatteryBinGenerator.wxs   # one-time in-place upgrade to v4 syntax
#        wix build -arch x64 GridfinityBatteryBinGenerator.wxs -o GridfinityBatteryBinGenerator-1.0.2-x64.msi
#
# Regenerate the .wxs after changing add-in files (needs Python 3):
#        python make_wxs.py
#
# Bump the version: edit VERSION in make_wxs.py AND AppVersion in
# GridfinityBatteryBinGenerator.bundle\PackageContents.xml, regenerate, rebuild.
# Never change UPGRADE_CODE - it is what makes upgrades replace old installs.
#
# Optional but recommended for distribution - Authenticode-sign the MSI:
#        signtool sign /fd SHA256 /td SHA256 /tr http://timestamp.digicert.com `
#                 /a GridfinityBatteryBinGenerator-1.0.2-x64.msi

$ErrorActionPreference = 'Stop'
python make_wxs.py
candle -arch x64 GridfinityBatteryBinGenerator.wxs
light GridfinityBatteryBinGenerator.wixobj -o GridfinityBatteryBinGenerator-1.0.2-x64.msi
Write-Host "Built GridfinityBatteryBinGenerator-1.0.2-x64.msi"

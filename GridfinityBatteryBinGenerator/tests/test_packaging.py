# Packaging consistency checks - no Fusion needed.
# Run: python3 tests/test_packaging.py
#
# Version and publisher strings live in four separate files that have to be
# bumped together. Nothing at runtime notices when one drifts, so it gets
# caught here instead of on a release page.

import json
import os
import re
import struct
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
ADDIN_DIR = os.path.dirname(TESTS_DIR)
REPO_ROOT = os.path.dirname(ADDIN_DIR)
INSTALLER_DIR = os.path.join(REPO_ROOT, 'installer')

# Never change this: the MSI upgrade code is what lets a new version replace
# an old install instead of sitting beside it in Add/Remove Programs.
EXPECTED_UPGRADE_CODE = '{6f2a8f10-9c53-4b7e-8d21-b7a4f0c2d9a1}'
EXPECTED_PUBLISHER = 'Bryan Gravely'

PASS = 0
FAIL = 0


def check(name, cond, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print('FAIL: {} {}'.format(name, detail))


def read(path):
    with open(path, 'r', encoding='utf-8') as handle:
        return handle.read()


manifestPath = os.path.join(ADDIN_DIR, 'GridfinityBatteryBinGenerator.manifest')
manifest = json.loads(read(manifestPath))
manifestVersion = manifest['version']
print('add-in manifest version:', manifestVersion)

check('manifest version looks like x.y.z',
      re.match(r'^\d+\.\d+\.\d+$', manifestVersion) is not None, manifestVersion)
check('manifest author is the publisher',
      manifest['author'] == EXPECTED_PUBLISHER, manifest['author'])
check('manifest runs on startup', manifest['runOnStartup'] is True)
check('manifest targets Fusion', manifest['autodeskProduct'] == 'Fusion360')

# main module must be named after the folder, or Fusion will not load it
check('main module matches folder name',
      os.path.isfile(os.path.join(ADDIN_DIR, 'GridfinityBatteryBinGenerator.py')))
check('bundled logo present',
      os.path.isfile(os.path.join(ADDIN_DIR, 'commands', 'commandCreateBatteryBin',
                                  'resources', 'logo.svg')))

changelog = read(os.path.join(REPO_ROOT, 'CHANGELOG.md'))
newest = re.search(r'^## (\d+\.\d+\.\d+)', changelog, re.M)
check('changelog has a version heading', newest is not None)
if newest:
    print('newest changelog entry:', newest.group(1))
    check('changelog matches manifest', newest.group(1) == manifestVersion,
          (newest.group(1), manifestVersion))

if not os.path.isdir(INSTALLER_DIR):
    print('installer/ not present - skipping installer checks')
else:
    packageContents = read(os.path.join(INSTALLER_DIR, 'PackageContents.xml'))
    appVersion = re.search(r'AppVersion="([^"]+)"', packageContents)
    componentVersion = re.search(r'<ComponentEntry[^>]*Version="([^"]+)"', packageContents)
    author = re.search(r'Author="([^"]+)"', packageContents)
    company = re.search(r'<CompanyDetails[^>]*Name="([^"]+)"', packageContents)
    moduleName = re.search(r'ModuleName="([^"]+)"', packageContents)

    check('PackageContents has AppVersion', appVersion is not None)
    check('PackageContents AppVersion matches manifest',
          appVersion and appVersion.group(1) == manifestVersion,
          appVersion and appVersion.group(1))
    check('PackageContents ComponentEntry version matches',
          componentVersion and componentVersion.group(1) == manifestVersion,
          componentVersion and componentVersion.group(1))
    check('PackageContents author is the publisher',
          author and author.group(1) == EXPECTED_PUBLISHER, author and author.group(1))
    check('PackageContents company is the publisher',
          company and company.group(1) == EXPECTED_PUBLISHER, company and company.group(1))
    check('PackageContents points at the real module',
          moduleName and moduleName.group(1).endswith(
              'Contents/GridfinityBatteryBinGenerator/GridfinityBatteryBinGenerator.py'),
          moduleName and moduleName.group(1))

    makeWxs = read(os.path.join(INSTALLER_DIR, 'make_wxs.py'))
    wxsVersion = re.search(r"^VERSION = '([^']+)'", makeWxs, re.M)
    manufacturer = re.search(r"^MANUFACTURER = '([^']+)'", makeWxs, re.M)
    upgradeCode = re.search(r"^UPGRADE_CODE = '([^']+)'", makeWxs, re.M)

    check('make_wxs VERSION matches manifest',
          wxsVersion and wxsVersion.group(1) == manifestVersion,
          wxsVersion and wxsVersion.group(1))
    check('MSI publisher matches the signing certificate name',
          manufacturer and manufacturer.group(1) == EXPECTED_PUBLISHER,
          manufacturer and manufacturer.group(1))
    check('MSI upgrade code is unchanged',
          upgradeCode and upgradeCode.group(1).lower() == EXPECTED_UPGRADE_CODE.lower(),
          upgradeCode and upgradeCode.group(1))

    # the installer must lay down the bare add-in folder, not a .bundle -
    # Fusion does not load a .bundle from the machine-wide ApplicationPlugins
    check('installer targets ApplicationPlugins',
          'ApplicationPlugins' in makeWxs)

    # install scope: one machine-wide copy under Program Files, covering every
    # Windows profile, rather than a per-user copy in AppData
    check('installs per-machine, not per-user',
          'InstallScope="perMachine"' in makeWxs, 'InstallScope')
    check('installs under 64-bit Program Files',
          'ProgramFiles64Folder' in makeWxs)
    check('no per-user install folder',
          'AppDataFolder' not in makeWxs and 'LocalAppDataFolder' not in makeWxs)
    check('installer payload is the bare add-in folder',
          ".bundle" not in re.search(r"^BUNDLE = .*$", makeWxs, re.M).group(0),
          re.search(r"^BUNDLE = .*$", makeWxs, re.M).group(0))

    # the installer UI is what confirms a successful install to the user
    check('installer requests WixUI_Minimal', 'WixUI_Minimal' in makeWxs)
    check('exit dialog carries follow-up text',
          'WIXUI_EXITDIALOGOPTIONALTEXT' in makeWxs)
    check('ARPNOMODIFY not redefined (WixUI_Minimal sets it)',
          'Property Id="ARPNOMODIFY"' not in makeWxs)
    # Add/Remove Programs entry carries the logo
    check('installer declares an ARP icon', 'ARPPRODUCTICON' in makeWxs)
    check('installer embeds the icon file', '<Icon Id="ProductIcon.ico"' in makeWxs)
    iconPath = os.path.join(INSTALLER_DIR, 'ProductIcon.ico')
    check('ARP icon file exists', os.path.isfile(iconPath), iconPath)
    if os.path.isfile(iconPath):
        with open(iconPath, 'rb') as handle:
            head = handle.read(6)
        # ICO header: reserved 0, type 1, then the image count
        check('ARP icon is a real .ico', head[:4] == b'\x00\x00\x01\x00', head[:4])
        check('ARP icon has several sizes', head[4] >= 3, head[4] if len(head) > 4 else None)

    # the Finish page tells people what to look for in Fusion, so it has to
    # name the command exactly as the menu does
    entryText = read(os.path.join(ADDIN_DIR, 'commands', 'commandCreateBatteryBin',
                                  'entry.py'))
    cmdName = re.search(r"^CMD_NAME = '([^']+)'", entryText, re.M)
    check('add-in declares a command name', cmdName is not None)
    wxsPath = os.path.join(INSTALLER_DIR, 'GridfinityBatteryBinGenerator.wxs')
    if cmdName and os.path.isfile(wxsPath):
        exitText = re.search(r'WIXUI_EXITDIALOGOPTIONALTEXT" Value="([^"]+)"', read(wxsPath))
        check('generated wxs carries exit text', exitText is not None)
        check('exit text names the command exactly',
              exitText and cmdName.group(1) in exitText.group(1),
              exitText and exitText.group(1))

    # branded installer artwork, at the sizes the WixUI dialogs expect
    for bmpName, expected in (('dlgbmp.bmp', (493, 312)), ('bannrbmp.bmp', (493, 58))):
        bmpPath = os.path.join(INSTALLER_DIR, bmpName)
        check(bmpName + ' exists', os.path.isfile(bmpPath), bmpPath)
        if os.path.isfile(bmpPath):
            with open(bmpPath, 'rb') as handle:
                header = handle.read(26)
            check(bmpName + ' is a BMP', header[:2] == b'BM', header[:2])
            width, height = struct.unpack('<ii', header[18:26])
            check(bmpName + ' is {}x{}'.format(*expected),
                  (width, abs(height)) == expected, (width, abs(height)))

    # --- shared plugin folder
    # Autodesk\ApplicationPlugins is shared by every Fusion add-in installed
    # this way. Windows Installer deletes a directory it created once the last
    # thing in it goes, so without permanent components holding these two open,
    # uninstalling took the shared folder with it whenever ours was the only
    # plugin present.
    check('a component holds the Autodesk folder open',
          'Id="cmpKeepAutodesk"' in makeWxs)
    check('a component holds the ApplicationPlugins folder open',
          'Id="cmpKeepAppPlugins"' in makeWxs)
    check('both folder-keepers are permanent', makeWxs.count('Permanent="yes"') == 2,
          makeWxs.count('Permanent="yes"'))
    check('both folder-keepers are installed',
          makeWxs.count('<ComponentRef Id="cmpKeepAutodesk"/>') == 1
          and makeWxs.count('<ComponentRef Id="cmpKeepAppPlugins"/>') == 1)
    check('the add-in folder itself is still removable',
          'Permanent' not in makeWxs.split('Id="dirBundle"')[1])
    # wixl silently ignores Component/@Permanent, so the linux build patches the
    # bit in afterwards and verifies it. If that step is lost, the flag in the
    # source becomes a comment that does nothing.
    buildLinux = read(os.path.join(INSTALLER_DIR, 'build-linux.sh'))
    check('the linux build sets the permanent bit wixl drops',
          'Attributes' in buildLinux and '= 272' in buildLinux)
    check('the linux build verifies the permanent bit took',
          '$4!=272' in buildLinux)

    check('linux build script present',
          os.path.isfile(os.path.join(INSTALLER_DIR, 'build-linux.sh')))
    check('make_wxs supports the WiX Toolset path', "'--wix' in sys.argv" in makeWxs)

    licensePath = os.path.join(INSTALLER_DIR, 'License.rtf')
    check('licence file for the installer exists', os.path.isfile(licensePath))
    if os.path.isfile(licensePath):
        licenseText = read(licensePath)
        check('licence file is rtf', licenseText.startswith('{\\rtf'))
        check('licence names the licence', 'CC BY-NC-SA' in licenseText)
        check('licence credits the bundled library', 'Lev Mishin' in licenseText)

    buildPs1 = read(os.path.join(INSTALLER_DIR, 'build.ps1'))
    check('build.ps1 documents the UI extension',
          'WixUIExtension' in buildPs1 and 'License.rtf' in buildPs1)
    check('build.ps1 mentions the icon file', 'ProductIcon.ico' in buildPs1)
    check('build.ps1 mentions the branded artwork',
          'dlgbmp.bmp' in buildPs1 and 'bannrbmp.bmp' in buildPs1)
    check('build.ps1 uses the WiX generator mode', 'make_wxs.py --wix' in buildPs1)
    check('build.ps1 references the current version',
          manifestVersion in buildPs1, manifestVersion)

print()
print('{} passed, {} failed'.format(PASS, FAIL))
sys.exit(1 if FAIL else 0)

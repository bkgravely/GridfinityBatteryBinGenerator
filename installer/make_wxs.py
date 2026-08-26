#!/usr/bin/env python3
"""Generate GridfinityBatteryBinGenerator.wxs from the .bundle tree.

WiX v3 syntax, compatible with both wixl (msitools) and the WiX Toolset on
Windows. One component per file with deterministic GUIDs (uuid5 of the
install path) so upgrades keep stable component identities.
"""
import os
import re
import sys
import uuid
import xml.sax.saxutils as sx

# The payload is the BARE add-in folder (py/manifest at its root) - Fusion loads
# this layout from C:\Program Files\Autodesk\ApplicationPlugins; the .bundle
# format is only used for the Autodesk App Store submission zip.
BUNDLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'GridfinityBatteryBinGenerator')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'GridfinityBatteryBinGenerator.wxs')

VERSION = '1.0.8'

# Emit WiX-Toolset-only elements (Windows builds). wixl rejects <WixVariable>
# and finds License.rtf / the dialog bitmaps by filename instead, so this is
# opt-in via `python make_wxs.py --wix`.
USE_WIX_VARIABLES = '--wix' in sys.argv


def commandName(fallback='Gridfinity Battery Bin'):
    """Read the command's display name out of the add-in itself, so the
    installer's closing instruction cannot drift from the Fusion menu entry."""
    here = os.path.dirname(os.path.abspath(__file__))
    relative = os.path.join('GridfinityBatteryBinGenerator', 'commands',
                            'commandCreateBatteryBin', 'entry.py')
    for candidate in (os.path.join(here, relative),
                      os.path.join(here, '..', relative)):
        try:
            with open(candidate, 'r', encoding='utf-8') as handle:
                found = re.search(r"^CMD_NAME = '([^']+)'", handle.read(), re.M)
        except OSError:
            continue
        if found:
            return found.group(1)
    return fallback


COMMAND_NAME = commandName()
EXIT_TEXT = 'Restart Autodesk Fusion, then find {} under Solid - Create.'.format(COMMAND_NAME)

UI_VARIABLES = ''
if USE_WIX_VARIABLES:
    UI_VARIABLES = (
        '\n        <WixVariable Id="WixUILicenseRtf" Value="License.rtf"/>'
        '\n        <WixVariable Id="WixUIDialogBmp" Value="dlgbmp.bmp"/>'
        '\n        <WixVariable Id="WixUIBannerBmp" Value="bannrbmp.bmp"/>')
# matches the code-signing certificate subject (CN=Bryan Gravely) so the
# Add/Remove Programs publisher and the signature agree
MANUFACTURER = 'Bryan Gravely'
PRODUCT_NAME = 'GridfinityBatteryBinGenerator for Autodesk Fusion'
UPGRADE_CODE = '{6f2a8f10-9c53-4b7e-8d21-b7a4f0c2d9a1}'  # never change this
NAMESPACE = uuid.UUID('a5e8c0de-1111-4222-8333-944445555666')

ids = set()


def makeId(prefix, path):
    base = prefix + '_' + path.replace('/', '_').replace('.', '_').replace('-', '_')
    base = ''.join(c if c.isalnum() or c == '_' else '_' for c in base)[:60]
    candidate = base
    i = 1
    while candidate in ids:
        candidate = '{}_{}'.format(base[:56], i)
        i += 1
    ids.add(candidate)
    return candidate


def emitDir(fsPath, relPath, indent):
    pad = '    ' * indent
    lines = []
    entries = sorted(os.listdir(fsPath))
    dirs = [e for e in entries if os.path.isdir(os.path.join(fsPath, e))]
    files = [e for e in entries if os.path.isfile(os.path.join(fsPath, e))]
    for f in files:
        rel = (relPath + '/' + f) if relPath else f
        compId = makeId('cmp', rel)
        fileId = makeId('fil', rel)
        guid = str(uuid.uuid5(NAMESPACE, 'pf64/Autodesk/ApplicationPlugins/GridfinityBatteryBinGenerator/' + rel)).upper()
        src = os.path.join('GridfinityBatteryBinGenerator', rel.replace('/', os.sep))
        lines.append('{}<Component Id="{}" Guid="{{{}}}">'.format(pad, compId, guid))
        lines.append('{}    <File Id="{}" Name="{}" Source="{}" KeyPath="yes"/>'.format(
            pad, fileId, sx.escape(f, {'"': '&quot;'}), sx.escape(src, {'"': '&quot;'})))
        lines.append('{}</Component>'.format(pad))
    for d in dirs:
        rel = (relPath + '/' + d) if relPath else d
        dirId = makeId('dir', rel)
        lines.append('{}<Directory Id="{}" Name="{}">'.format(pad, dirId, sx.escape(d, {'"': '&quot;'})))
        lines.extend(emitDir(os.path.join(fsPath, d), rel, indent + 1))
        lines.append('{}</Directory>'.format(pad))
    return lines


body = emitDir(BUNDLE, '', 7)
compRefs = '\n'.join('            <ComponentRef Id="{}"/>'.format(i) for i in sorted(ids) if i.startswith('cmp'))

wxs = '''<?xml version="1.0" encoding="utf-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
    <Product Id="*"
             Name="{name}"
             Language="1033"
             Version="{version}"
             Manufacturer="{manufacturer}"
             UpgradeCode="{upgrade}">
        <Package InstallerVersion="500" Compressed="yes" InstallScope="perMachine"
                 Description="{name} {version}"
                 Manufacturer="{manufacturer}"/>
        <MediaTemplate EmbedCab="yes"/>
        <!-- WixUI_Minimal: licence page, progress, and a Finish page that
             actually confirms the install worked. Requires the UI extension
             at build time. wixl picks up License.rtf from the build folder;
             the WiX Toolset needs it passed explicitly (see build.ps1). -->
        <UIRef Id="WixUI_Minimal"/>{uiVariables}
        <Property Id="WIXUI_EXITDIALOGOPTIONALTEXT" Value="{exitText}"/>
        <MajorUpgrade AllowSameVersionUpgrades="yes"
                      DowngradeErrorMessage="A newer version of [ProductName] is already installed."/>
        <!-- ARPNOMODIFY is set by WixUI_Minimal; defining it here too
             collides on the Property table primary key. -->
        <Property Id="ARPCOMMENTS" Value="Gridfinity battery storage bin generator add-in for Autodesk Fusion"/>
        <Property Id="ARPURLINFOABOUT" Value="https://github.com/bkgravely/GridfinityBatteryBinGenerator"/>
        <!-- icon shown beside the entry in Add/Remove Programs -->
        <Icon Id="ProductIcon.ico" SourceFile="ProductIcon.ico"/>
        <Property Id="ARPPRODUCTICON" Value="ProductIcon.ico"/>
        <Directory Id="TARGETDIR" Name="SourceDir">
            <Directory Id="ProgramFiles64Folder">
                <Directory Id="dirAutodesk" Name="Autodesk">
                    <Directory Id="dirAppPlugins" Name="ApplicationPlugins">
                        <Directory Id="dirBundle" Name="GridfinityBatteryBinGenerator">
{body}
                        </Directory>
                    </Directory>
                </Directory>
            </Directory>
        </Directory>
        <Feature Id="MainFeature" Title="{name}" Level="1">
{comprefs}
        </Feature>
    </Product>
</Wix>
'''.format(name=PRODUCT_NAME, version=VERSION, manufacturer=MANUFACTURER,
           uiVariables=UI_VARIABLES, exitText=EXIT_TEXT,
           upgrade=UPGRADE_CODE, body='\n'.join(body), comprefs=compRefs)

with open(OUT, 'w') as f:
    f.write(wxs)
print('wrote', OUT, '-', wxs.count('<Component '), 'components')

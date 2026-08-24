#!/usr/bin/env python3
"""Generate GridfinityBatteryBinGenerator.wxs from the .bundle tree.

WiX v3 syntax, compatible with both wixl (msitools) and the WiX Toolset on
Windows. One component per file with deterministic GUIDs (uuid5 of the
install path) so upgrades keep stable component identities.
"""
import os
import uuid
import xml.sax.saxutils as sx

BUNDLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'GridfinityBatteryBinGenerator.bundle')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'GridfinityBatteryBinGenerator.wxs')

VERSION = '1.0.1'
MANUFACTURER = 'Gravlaxy'
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
        guid = str(uuid.uuid5(NAMESPACE, 'pf64/Autodesk/ApplicationPlugins/GridfinityBatteryBinGenerator.bundle/' + rel)).upper()
        src = os.path.join('GridfinityBatteryBinGenerator.bundle', rel.replace('/', os.sep))
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
        <MajorUpgrade AllowSameVersionUpgrades="yes"
                      DowngradeErrorMessage="A newer version of [ProductName] is already installed."/>
        <Property Id="ARPNOMODIFY" Value="1"/>
        <Property Id="ARPCOMMENTS" Value="Gridfinity battery storage bin generator add-in for Autodesk Fusion"/>
        <Directory Id="TARGETDIR" Name="SourceDir">
            <Directory Id="ProgramFiles64Folder">
                <Directory Id="dirAutodesk" Name="Autodesk">
                    <Directory Id="dirAppPlugins" Name="ApplicationPlugins">
                        <Directory Id="dirBundle" Name="GridfinityBatteryBinGenerator.bundle">
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
           upgrade=UPGRADE_CODE, body='\n'.join(body), comprefs=compRefs)

with open(OUT, 'w') as f:
    f.write(wxs)
print('wrote', OUT, '-', wxs.count('<Component '), 'components')

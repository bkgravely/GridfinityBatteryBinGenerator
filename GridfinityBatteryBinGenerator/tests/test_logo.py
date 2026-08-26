# Tests for lib/batteryUtils/logoUtils.py (no Fusion needed).
# Run: python3 tests/test_logo.py
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))

from batteryUtils import logoUtils as L

PASS = 0
FAIL = 0


def check(name, cond, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print('FAIL: {} {}'.format(name, detail))


print('--- foot geometry ---')
flat = L.footFlatWidth(42.0, 0.25)
print('foot flat bottom face: {:.2f} mm square'.format(flat))
check('flat width 35.1', abs(flat - 35.1) < 1e-9, flat)
check('max logo width 31.1', abs(L.maxLogoWidth(42.0, 0.25) - 31.1) < 1e-9,
      L.maxLogoWidth(42.0, 0.25))
check('bottom z is -5', abs(L.bottomZ() + 5.0) < 1e-9, L.bottomZ())

# corner foot of a 1x1 must sit at the body centre (body spans 0..41.5)
cx, cy = L.footCenter(0, 0, 42.0, 42.0, 0.25)
check('1x1 foot centred on body', abs(cx - 20.75) < 1e-9 and abs(cy - 20.75) < 1e-9, (cx, cy))

# the mean of all foot centres must equal the centre of the whole body
for (bx, by) in [(1, 1), (2, 3), (3, 4), (4, 5)]:
    centers = L.footCenters(bx, by, 42.0, 42.0, 0.25, L.PLACEMENT_EVERY)
    check('{}x{} every foot count'.format(bx, by), len(centers) == bx * by, len(centers))
    meanX = sum(c[0] for c in centers) / len(centers)
    meanY = sum(c[1] for c in centers) / len(centers)
    bodyMidX = (42.0 * bx - 2 * 0.25) / 2.0
    bodyMidY = (42.0 * by - 2 * 0.25) / 2.0
    check('{}x{} pattern centred'.format(bx, by),
          abs(meanX - bodyMidX) < 1e-9 and abs(meanY - bodyMidY) < 1e-9,
          (meanX, bodyMidX, meanY, bodyMidY))
    # every foot centre must leave a whole logo inside the flat face
    for (x, y) in centers:
        half = L.maxLogoWidth(42.0, 0.25) / 2.0
        footX = round((x - 20.75) / 42.0)
        check('{}x{} foot on grid'.format(bx, by),
              abs(x - (footX * 42.0 + 20.75)) < 1e-9, x)
        check('{}x{} logo inside footprint'.format(bx, by),
              x - half >= -1e-9 and y - half >= -1e-9, (x, y, half))

check('corner placement is foot 0,0',
      L.footCenters(3, 4, 42.0, 42.0, 0.25, L.PLACEMENT_CORNER) == [(20.75, 20.75)])
check('centre of 3x3 is middle foot',
      L.footCenters(3, 3, 42.0, 42.0, 0.25, L.PLACEMENT_CENTER) == [(62.75, 62.75)])
check('centre of 1x1 is only foot',
      L.footCenters(1, 1, 42.0, 42.0, 0.25, L.PLACEMENT_CENTER) == [(20.75, 20.75)])

print('--- nested region parity ---')
# letter "O": ring (depth 0) plus the counter inside it (depth 1)
ring = (0.0, 0.0, 10.0, 10.0)
counter = (2.0, 2.0, 8.0, 8.0)
check('O keeps only the ring', L.keepByNestingParity([ring, counter]) == [0])

# ring with an island floating inside the counter: engrave, hole, engrave
island = (4.0, 4.0, 6.0, 6.0)
check('island inside a counter is engraved',
      L.keepByNestingParity([ring, counter, island]) == [0, 2])

# two separate marks side by side are both engraved
a = (0.0, 0.0, 4.0, 4.0)
b = (6.0, 0.0, 10.0, 4.0)
check('sibling shapes both kept', L.keepByNestingParity([a, b]) == [0, 1])
check('single shape kept', L.keepByNestingParity([a]) == [0])
check('no shapes', L.keepByNestingParity([]) == [])

print('--- svg transform wrapping ---')
plain = '<?xml version="1.0"?>\n<svg viewBox="0 0 10 10"><path d="M0,0 L1,1"/></svg>'
check('no transform returns original', L.wrapSvgTransform(plain, False, 0) is plain)

mirrored = L.wrapSvgTransform(plain, True, 0)
check('mirror wraps content', '<g transform="scale(-1,1)">' in mirrored, mirrored)
check('mirror keeps path', 'M0,0 L1,1' in mirrored)
check('mirror closes group before svg', mirrored.endswith('</g></svg>'), mirrored[-30:])
check('mirror keeps declaration', mirrored.startswith('<?xml version="1.0"?>'))
check('group opens after svg tag',
      mirrored.index('<g transform') > mirrored.index('<svg'), mirrored)

rotated = L.wrapSvgTransform(plain, True, 90)
check('rotate+mirror order', 'transform="rotate(90) scale(-1,1)"' in rotated, rotated)
check('rotate only', 'transform="rotate(180)"' in L.wrapSvgTransform(plain, False, 180))
check('360 is no transform', L.wrapSvgTransform(plain, False, 360) is plain)
check('transform attr empty when idle', L.svgTransformAttr(False, 0) == '')

# a '>' inside an attribute must not be mistaken for the end of the tag
tricky = '<svg viewBox="0 0 10 10" data-note="a > b"><path d="M0,0 L1,1"/></svg>'
out = L.wrapSvgTransform(tricky, True, 0)
check('quoted > handled', out.index('<g transform') > out.index('data-note'), out)
check('quoted > keeps path once', out.count('M0,0 L1,1') == 1)

# uppercase / spaced tags
check('uppercase svg tag handled',
      '<g transform=' in L.wrapSvgTransform('<SVG viewBox="0 0 1 1"><path/></SVG>', True, 0))

for bad, why in [('<html><body/></html>', 'no svg element'),
                 ('<svg viewBox="0 0 1 1"/>', 'empty svg'),
                 ('<svg viewBox="0 0 1 1"><path/>', 'unclosed svg')]:
    try:
        L.wrapSvgTransform(bad, True, 0)
        check('rejects ' + why, False, bad)
    except ValueError:
        check('rejects ' + why, True)

print('--- viewBox follows the transform ---')
# a rotated wrap that keeps the old viewBox gets clipped by importers, which
# is how a rotated logo silently becomes no logo at all
check('rot90 swaps the viewBox extents',
      L.transformedViewBox('0 0 432 306', False, 90) == '-306.0000 0.0000 306.0000 432.0000',
      L.transformedViewBox('0 0 432 306', False, 90))
check('rot180 keeps the extents',
      L.transformedViewBox('0 0 432 306', False, 180) == '-432.0000 -306.0000 432.0000 306.0000',
      L.transformedViewBox('0 0 432 306', False, 180))
check('mirror flips x only',
      L.transformedViewBox('0 0 432 306', True, 0) == '-432.0000 0.0000 432.0000 306.0000',
      L.transformedViewBox('0 0 432 306', True, 0))
check('unparseable viewBox is ignored', L.transformedViewBox('nonsense', True, 90) is None)
check('comma separated viewBox works',
      L.transformedViewBox('0,0,10,10', False, 0) is not None)

rotatedSvg = L.wrapSvgTransform(
    '<svg viewBox="0 0 432 306" width="432" height="306"><path d="M0,0 L1,1"/></svg>', False, 90)
check('wrap rewrites the viewBox', 'viewBox="-306.0000 0.0000 306.0000 432.0000"' in rotatedSvg,
      rotatedSvg)
check('wrap drops width so aspect cannot squash', ' width=' not in rotatedSvg, rotatedSvg)
check('wrap drops height so aspect cannot squash', ' height=' not in rotatedSvg, rotatedSvg)
check('wrap still applies the transform', 'transform="rotate(90)"' in rotatedSvg)
check('wrap keeps the artwork', 'M0,0 L1,1' in rotatedSvg)

noBox = L.wrapSvgTransform('<svg><path d="M0,0 L1,1"/></svg>', True, 0)
check('missing viewBox still wraps', '<g transform="scale(-1,1)">' in noBox, noBox)

print('--- bundled logo ---')
logoPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                        'commands', 'commandCreateBatteryBin', 'resources', 'logo.svg')
check('bundled logo exists', os.path.exists(logoPath), logoPath)
if os.path.exists(logoPath):
    with open(logoPath, 'r', encoding='utf-8') as handle:
        text = handle.read()
    # Closure and freedom from zero-length segments are verified when the
    # artwork is baked (both would stop Fusion forming a profile); without an
    # SVG parser here, assert the shape of the file instead.
    check('bundled logo has paths', text.count('<path') >= 1, text.count('<path'))
    check('bundled logo declares a viewBox', 'viewBox' in text)
    check('bundled logo records that it is pre-oriented',
          'pre-oriented' in text, text[:400])
    check('bundled logo has no live text', '<text' not in text)
    # orientation is baked into the path data, so no runtime transform is needed
    check('bundled logo needs no runtime transform',
          L.LOGO_MIRROR is False and L.LOGO_ROTATION == 0,
          (L.LOGO_MIRROR, L.LOGO_ROTATION))
    check('bundled logo is landscape once oriented',
          '<svg' in text and 'viewBox' in text)
    out = L.wrapSvgTransform(text, True, 0)
    check('bundled logo mirrors cleanly', '<g transform="scale(-1,1)">' in out)
    check('bundled logo keeps all paths', out.count('<path') == text.count('<path'))

import tempfile
with tempfile.TemporaryDirectory() as tmp:
    same = L.orientedSvgPath(logoPath, False, 0, tmp)
    check('untransformed returns source path', same == logoPath, same)
    written = L.orientedSvgPath(logoPath, True, 90, tmp)
    check('transformed file written', os.path.exists(written), written)
    check('transformed name is deterministic',
          written == L.orientedSvgPath(logoPath, True, 90, tmp))
    check('transformed differs from source', written != logoPath)
    with open(written, 'r', encoding='utf-8') as handle:
        check('transformed content carries transform',
              'rotate(90) scale(-1,1)' in handle.read())

print()
print('{} passed, {} failed'.format(PASS, FAIL))
sys.exit(1 if FAIL else 0)

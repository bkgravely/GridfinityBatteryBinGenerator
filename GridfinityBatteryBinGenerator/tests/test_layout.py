# Local unit tests for lib/batteryUtils/layout.py (no Fusion needed).
# Run: python3 tests/test_layout.py
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from batteryUtils import layout
from batteryUtils import batteryDefs

PASS = 0
FAIL = 0


def check(name, cond, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print('FAIL: {} {}'.format(name, detail))


def floorDims(binX, binY, wallMm=2.15, xyClear=0.25, baseUnit=42.0):
    w = baseUnit * binX - 2 * xyClear - 2 * wallMm
    l = baseUnit * binY - 2 * xyClear - 2 * wallMm
    return w, l


def verifyLayout(name, res, floorW, floorL, diaOrX, spacing, wallClear, diaOrY=None):
    if res is None:
        return
    sx = diaOrX
    sy = diaOrY if diaOrY is not None else diaOrX
    # wall clearance (rect: axis-aligned; round: sx == sy == dia)
    for (x, y) in res['centers']:
        check(name + ' wallClear x-', x - sx / 2 >= wallClear - 1e-6, (x, y))
        check(name + ' wallClear x+', floorW - x - sx / 2 >= wallClear - 1e-6, (x, y))
        check(name + ' wallClear y-', y - sy / 2 >= wallClear - 1e-6, (x, y))
        check(name + ' wallClear y+', floorL - y - sy / 2 >= wallClear - 1e-6, (x, y))
    # min spacing between slots
    cs = res['centers']
    for i in range(len(cs)):
        for j in range(i + 1, len(cs)):
            dx = abs(cs[i][0] - cs[j][0])
            dy = abs(cs[i][1] - cs[j][1])
            if diaOrY is None:
                gap = math.hypot(dx, dy) - diaOrX
            else:
                # axis-aligned rectangles: separation along an axis
                gapx = dx - sx
                gapy = dy - sy
                gap = max(gapx, gapy)
            check(name + ' spacing', gap >= spacing - 1e-6,
                  'i={} j={} gap={:.3f}'.format(i, j, gap))
    # centered
    xs = [c[0] for c in cs]
    ys = [c[1] for c in cs]
    check(name + ' centeredX',
          abs((min(xs) - sx / 2) - (floorW - max(xs) - sx / 2)) < 1e-6)
    check(name + ' centeredY',
          abs((min(ys) - sy / 2) - (floorL - max(ys) - sy / 2)) < 1e-6)
    check(name + ' count matches centers', res['count'] == len(cs))


print('--- round layouts, all battery types, bin sizes 1x1..5x5 ---')
for bat in ['AAA', 'AA', 'CR123', '18650']:
    d = batteryDefs.BATTERY_DEFAULTS[bat]
    for bx in range(1, 6):
        for by in range(1, 6):
            fw, fl = floorDims(bx, by)
            res = layout.computeRoundLayout(fw, fl, d['slotDiaLen'], 3.0, 5.0)
            name = '{} {}x{}'.format(bat, bx, by)
            check(name + ' fits', res is not None and res['count'] >= 1, res)
            verifyLayout(name, res, fw, fl, d['slotDiaLen'], 3.0, 5.0)

print('--- 9V rect layouts ---')
d = batteryDefs.BATTERY_DEFAULTS['9V']
for bx in range(1, 6):
    for by in range(1, 6):
        fw, fl = floorDims(bx, by)
        res = layout.computeRectLayout(fw, fl, d['slotDiaLen'], d['slotWidth'], 3.0, 5.0)
        name = '9V {}x{}'.format(bx, by)
        if (bx, by) == (1, 1):
            # 27.4 slot + 2x5 clearance = 37.4 > 37.2 floor: nothing fits, by design
            check(name + ' correctly reports no fit', res is None, res)
            continue
        check(name + ' fits', res is not None and res['count'] >= 1, res)
        if res:
            verifyLayout(name, res, fw, fl, res['slotX'], 3.0, 5.0, res['slotY'])

print('--- hex beats or ties square for AA 2x3 ---')
fw, fl = floorDims(2, 3)
res = layout.computeRoundLayout(fw, fl, 14.75, 3.0, 5.0)
print('AA 2x3 floor {:.2f}x{:.2f}: {} -> {}'.format(fw, fl, res['count'], res['desc']))
check('AA 2x3 uses hex', 'hex' in res['desc'], res['desc'])
check('AA 2x3 count 25', res['count'] == 25, res['count'])

print('--- degenerate: too small floor ---')
res = layout.computeRoundLayout(20.0, 20.0, 14.75, 3.0, 5.0)
check('tiny floor none', res is None, res)
res = layout.computeRoundLayout(24.75, 24.75, 14.75, 3.0, 5.0)
check('exactly one fits', res is not None and res['count'] == 1, res)

print('--- auto height + fit checks with default tables ---')
expectedU = {'AAA': 8, 'AA': 9, 'CR123': 6, '9V': 9, '18650': 11}
for bat in batteryDefs.BATTERY_TYPES:
    d = batteryDefs.BATTERY_DEFAULTS[bat]
    u = layout.autoMinHeightUnits(d['ledgeDrop'], d['slotDepth'], d['tipDepth'],
                                  batteryDefs.DEFAULT_BASE_DIP_ALLOWANCE)
    fc = layout.fitCheck(u, d['ledgeDrop'], d['slotDepth'], d['tipDepth'],
                         d['batteryLength'], batteryDefs.DEFAULT_HEADROOM)
    print('{:6s} u={:2d} ({}mm total) wallTop={:5.1f} ledgeZ={:5.1f} '
          'slotBottom={:5.1f} recessBottom={:5.1f} batteryTop={:5.1f} '
          'margin={:+.2f} baseDip={:.2f}'.format(
              bat, u, u * 7, fc['wallTop'], fc['ledgeZ'], fc['slotBottomZ'],
              fc['recessBottomZ'], fc['batteryTop'], fc['margin'], fc['baseDip']))
    check(bat + ' auto units', u == expectedU[bat], u)
    check(bat + ' stackable', fc['margin'] >= -1e-6, fc)
    check(bat + ' dip within allowance',
          fc['baseDip'] <= batteryDefs.DEFAULT_BASE_DIP_ALLOWANCE + 1e-6, fc)
    # one more unit never hurts, one fewer must violate the dip allowance
    fcLess = layout.fitCheck(u - 1, d['ledgeDrop'], d['slotDepth'], d['tipDepth'],
                             d['batteryLength'], batteryDefs.DEFAULT_HEADROOM)
    check(bat + ' minimality', fcLess['baseDip'] > batteryDefs.DEFAULT_BASE_DIP_ALLOWANCE, fcLess)

print('--- counts summary (defaults, wall 2.15) ---')
for bat in batteryDefs.BATTERY_TYPES:
    d = batteryDefs.BATTERY_DEFAULTS[bat]
    row = []
    for (bx, by) in [(1, 1), (2, 2), (2, 3), (3, 4), (4, 5)]:
        fw, fl = floorDims(bx, by)
        if d['isRound']:
            res = layout.computeRoundLayout(fw, fl, d['slotDiaLen'], 3.0, 5.0)
        else:
            res = layout.computeRectLayout(fw, fl, d['slotDiaLen'], d['slotWidth'], 3.0, 5.0)
        row.append('{}x{}:{}'.format(bx, by, res['count'] if res else 0))
    print('{:6s} {}'.format(bat, '  '.join(row)))

print()
print('{} passed, {} failed'.format(PASS, FAIL))
sys.exit(1 if FAIL else 0)

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


def _raises(call, exc=ValueError):
    try:
        call()
    except exc:
        return True
    return False


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

print('--- 9V rect layouts (mixed orientations allowed) ---')
d = batteryDefs.BATTERY_DEFAULTS['9V']


def verifyRect(name, res, floorW, floorL, spacing, wallClear):
    """Every slot inside the floor with clearance, and no two slots closer
    than `spacing`. Works for mixed orientations, where each slot has its
    own footprint."""
    slots = list(zip(res['centers'], res['slotSizes']))
    for ((x, y), (w, l)) in slots:
        check(name + ' inside floor',
              x - w/2 >= wallClear - 1e-6 and floorW - x - w/2 >= wallClear - 1e-6
              and y - l/2 >= wallClear - 1e-6 and floorL - y - l/2 >= wallClear - 1e-6,
              (x, y, w, l))
    for i in range(len(slots)):
        (xi, yi), (wi, li) = slots[i]
        for j in range(i + 1, len(slots)):
            (xj, yj), (wj, lj) = slots[j]
            gapX = abs(xi - xj) - (wi + wj) / 2.0
            gapY = abs(yi - yj) - (li + lj) / 2.0
            check(name + ' slots kept apart', max(gapX, gapY) >= spacing - 1e-6,
                  (i, j, gapX, gapY))
    xs = [x for ((x, y), s) in slots]; ys = [y for ((x, y), s) in slots]
    lo = min(x - w/2 for ((x, y), (w, l)) in slots)
    hi = max(x + w/2 for ((x, y), (w, l)) in slots)
    check(name + ' centred in x', abs(lo - (floorW - hi)) < 1e-6, (lo, floorW - hi))
    check(name + ' count matches slots', res['count'] == len(slots))
    check(name + ' sizes parallel to centres',
          len(res['centers']) == len(res['slotSizes']))


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
            verifyRect(name, res, fw, fl, 3.0, 5.0)

# mixed packing must never do worse than the best uniform grid, and should
# beat it where the offcut is wide enough to turn a row sideways
expectedMixed = {(2, 3): 11, (3, 3): 18, (3, 4): 26, (2, 2): 6, (4, 4): 35}
for (bx, by), expected in expectedMixed.items():
    fw, fl = floorDims(bx, by)
    res = layout.computeRectLayout(fw, fl, d['slotDiaLen'], d['slotWidth'], 3.0, 5.0)
    check('9V {}x{} packs {}'.format(bx, by, expected), res['count'] == expected,
          (res['count'], res['desc']))

# a mixed result really does use both orientations
res = layout.computeRectLayout(*floorDims(3, 3), d['slotDiaLen'], d['slotWidth'], 3.0, 5.0)
orientations = set(res['slotSizes'])
check('3x3 mixes two orientations', len(orientations) == 2, orientations)
print('9V 3x3: {} slots :: {}'.format(res['count'], res['desc']))

# a square slot can never benefit from turning, so it must stay uniform
sq = layout.computeRectLayout(*floorDims(3, 3), 20.0, 20.0, 3.0, 5.0)
check('square slots stay uniform', len(set(sq['slotSizes'])) == 1, set(sq['slotSizes']))

print('--- uniform grids (mixed orientations switched off) ---')
# 4x4 is the case where a plain grid already fills the floor, so mixing wins
# nothing and the two settings agree
expectedUniform = {(2, 2): 6, (2, 3): 10, (3, 3): 15, (3, 4): 25, (4, 4): 35}
for bx in range(1, 6):
    for by in range(1, 6):
        fw, fl = floorDims(bx, by)
        res = layout.computeRectLayout(fw, fl, d['slotDiaLen'], d['slotWidth'],
                                       3.0, 5.0, False)
        mixed = layout.computeRectLayout(fw, fl, d['slotDiaLen'], d['slotWidth'],
                                         3.0, 5.0, True)
        name = '9V {}x{} uniform'.format(bx, by)
        if (bx, by) == (1, 1):
            check(name + ' correctly reports no fit', res is None, res)
            continue
        check(name + ' fits', res is not None and res['count'] >= 1, res)
        verifyRect(name, res, fw, fl, 3.0, 5.0)
        # one footprint for the whole bin, and never more than the mixed result
        check(name + ' uses a single orientation',
              len(set(res['slotSizes'])) == 1, set(res['slotSizes']))
        check(name + ' never beats mixed', res['count'] <= mixed['count'],
              (res['count'], mixed['count']))
        if (bx, by) in expectedUniform:
            check('{} packs {}'.format(name, expectedUniform[(bx, by)]),
                  res['count'] == expectedUniform[(bx, by)], (res['count'], res['desc']))

# round layouts have no orientation to mix, so the flag must not reach them
check('uniform desc names a plain grid',
      'plus' not in layout.computeRectLayout(*floorDims(3, 3), d['slotDiaLen'],
                                             d['slotWidth'], 3.0, 5.0, False)['desc'])

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
expectedU = {'AAA': 8, 'AA': 9, 'CR123': 7, '9V': 9, '18650': 11}
for bat in batteryDefs.BATTERY_TYPES:
    d = batteryDefs.BATTERY_DEFAULTS[bat]
    u = layout.autoMinHeightUnits(d['ledgeDrop'], d['slotDepth'], d['tipDepth'],
                                  batteryDefs.DEFAULT_MIN_FLOOR_THICKNESS)
    fc = layout.fitCheck(u, d['ledgeDrop'], d['slotDepth'], d['tipDepth'],
                         d['batteryLength'], batteryDefs.DEFAULT_HEADROOM)
    print('{:6s} u={:2d} ({}mm total) wallTop={:5.1f} ledgeZ={:5.1f} '
          'slotBottom={:5.1f} recessBottom={:5.1f} batteryTop={:5.1f} '
          'margin={:+.2f} floor={:.2f}'.format(
              bat, u, u * 7, fc['wallTop'], fc['ledgeZ'], fc['slotBottomZ'],
              fc['recessBottomZ'], fc['batteryTop'], fc['margin'],
              fc['floorThickness']))
    check(bat + ' auto units', u == expectedU[bat], u)
    check(bat + ' stackable', fc['margin'] >= -1e-6, fc)
    # nothing may reach the underside of the body: the feet leave gaps there
    check(bat + ' keeps a solid floor',
          fc['floorThickness'] >= batteryDefs.DEFAULT_MIN_FLOOR_THICKNESS - 1e-6, fc)
    check(bat + ' never breaks through the bottom', fc['recessBottomZ'] > 0, fc)
    # one more unit never hurts, one fewer must violate the dip allowance
    fcLess = layout.fitCheck(u - 1, d['ledgeDrop'], d['slotDepth'], d['tipDepth'],
                             d['batteryLength'], batteryDefs.DEFAULT_HEADROOM)
    check(bat + ' minimality',
          fcLess['floorThickness'] < batteryDefs.DEFAULT_MIN_FLOOR_THICKNESS, fcLess)

print('--- corner label tab ---')
check('two letters need a smaller shelf',
      layout.tabLegForText('LI', 2.8, 0.7) < layout.tabLegForText('ALK', 2.8, 0.7))
# character widths, not character counts: I is a third the width of W, so
# which letters are in the code moves the shelf as much as how many
check('a narrow three-letter code beats a wide two-letter one',
      layout.tabLegForText('III', 5.0, 0.6) < layout.tabLegForText('WW', 5.0, 0.6),
      (layout.tabLegForText('III', 5.0, 0.6), layout.tabLegForText('WW', 5.0, 0.6)))
check('an unknown character is sized as the widest there is',
      abs(layout.textWidthRatio(chr(0x2022)) - layout.CHAR_WIDTH_FALLBACK) < 1e-9)
# measured against the font itself: "ALK" at 7.5 mm is 22.4 mm wide, not the
# 15.3 mm a flat 0.68 average gave - the error that ran the K into the wall
check('ALK at 7.5 mm measures 22.4 mm wide',
      abs(layout.tabTextWidth('ALK', 7.5) - 22.41) < 0.05,
      layout.tabTextWidth('ALK', 7.5))
check('leg and text height invert each other',
      abs(layout.tabTextHeightForLeg(layout.tabLegForText('ALK', 2.8, 0.7), 'ALK', 0.7)
          - 2.8) < 1e-9)
check('unknown corner is rejected',
      _raises(lambda: layout.tabTriangle(80.0, 100.0, 10.0, 'middle')))
for corner, expected in (('Back left', [(0.0, 100.0), (10.0, 100.0), (0.0, 90.0)]),
                         ('Back right', [(80.0, 100.0), (70.0, 100.0), (80.0, 90.0)]),
                         ('Front left', [(0.0, 0.0), (10.0, 0.0), (0.0, 10.0)]),
                         ('Front right', [(80.0, 0.0), (70.0, 0.0), (80.0, 10.0)])):
    check('triangle on the ' + corner,
          layout.tabTriangle(80.0, 100.0, 10.0, corner) == expected,
          layout.tabTriangle(80.0, 100.0, 10.0, corner))

# the guarantee: a corner triangle within twice the wall clearance cannot
# reach a slot, whatever the battery, bin size or corner
for clearance in (4.0, 5.0, 6.0):
    freeLeg = layout.freeTabLeg(clearance)
    for bat in batteryDefs.BATTERY_TYPES:
        d = batteryDefs.BATTERY_DEFAULTS[bat]
        for (bx, by) in [(1, 1), (1, 2), (2, 2), (2, 3), (3, 3), (3, 4), (4, 5), (5, 5)]:
            fw, fl = floorDims(bx, by)
            if d['isRound']:
                res = layout.computeRoundLayout(fw, fl, d['slotDiaLen'], 3.0, clearance)
            else:
                res = layout.computeRectLayout(fw, fl, d['slotDiaLen'], d['slotWidth'],
                                               3.0, clearance)
            if res is None or freeLeg >= min(fw, fl):
                continue
            for corner in layout.TAB_CORNERS:
                tri = layout.tabTriangle(fw, fl, freeLeg, corner)
                trimmed = layout.removeSlotsUnderTab(res, tri)
                check('{} {}x{} {} shelf at clearance {} is free'.format(
                          bat, bx, by, corner, clearance),
                      trimmed is not None and trimmed['blocked'] == 0,
                      trimmed and trimmed['blocked'])
                check('{} {}x{} {} keeps every slot'.format(bat, bx, by, corner),
                      trimmed['count'] == res['count'])
                check('{} {}x{} {} slots do not move'.format(bat, bx, by, corner),
                      trimmed['centers'] == res['centers'])

# and one deliberately oversized shelf must be caught rather than ignored
fw, fl = floorDims(2, 3)
d = batteryDefs.BATTERY_DEFAULTS['AA']
res = layout.computeRoundLayout(fw, fl, d['slotDiaLen'], 3.0, 5.0)
big = layout.removeSlotsUnderTab(res, layout.tabTriangle(fw, fl, 22.0, 'Back left'))
check('an oversized shelf does cover slots', big['blocked'] > 0, big['blocked'])
check('oversized shelf count matches', big['count'] == res['count'] - big['blocked'])
check('nothing left under an oversized shelf',
      layout.slotsUnder(big, layout.tabTriangle(fw, fl, 22.0, 'Back left')) == [])

# the lettering has to sit inside the triangle it was sized for: the baseline
# runs parallel to the hypotenuse, and the text band reaches inwards from it
for corner in layout.TAB_CORNERS:
    leg = layout.tabLegForText('ALK', 2.8, 0.7)
    tri = layout.tabTriangle(fw, fl, leg, corner)
    (sx, sy), (ex, ey) = layout.tabTextBaseline(fw, fl, leg, 0.7, corner)
    cornerPt = tri[0]
    midX = (tri[1][0] + tri[2][0]) / 2.0
    midY = (tri[1][1] + tri[2][1]) / 2.0
    inX, inY = cornerPt[0] - midX, cornerPt[1] - midY
    inLen = math.hypot(inX, inY)
    inX, inY = inX / inLen, inY / inLen
    ux, uy = ex - sx, ey - sy
    check(corner + ' baseline is parallel to the hypotenuse',
          abs(ux * (tri[2][1] - tri[1][1]) - uy * (tri[2][0] - tri[1][0])) < 1e-9)
    check(corner + ' text falls towards the corner',
          ux * inY - uy * inX > 0, (ux, uy, inX, inY))
    # the lettering is centred on the baseline: check its four corners, not
    # the ends of the line, because the triangle narrows between them
    runLen = math.hypot(ux, uy)
    dirX, dirY = ux / runLen, uy / runLen
    midBaseX, midBaseY = (sx + ex) / 2.0, (sy + ey) / 2.0
    halfText = layout.tabTextWidth('ALK', 2.8) / 2.0
    band = []
    for along in (-halfText, halfText):
        for deep in (0.0, 2.8):
            band.append((midBaseX + dirX * along + inX * deep,
                         midBaseY + dirY * along + inY * deep))
    check(corner + ' lettering stays inside the triangle',
          all(abs(px - cornerPt[0]) + abs(py - cornerPt[1]) <= leg + 1e-6
              for (px, py) in band), band)
    check(corner + ' lettering is inside the floor',
          all(-1e-6 <= px <= fw + 1e-6 and -1e-6 <= py <= fl + 1e-6
              for (px, py) in band), band)
    check(corner + ' baseline is long enough for the text',
          math.hypot(ux, uy) >= layout.tabTextWidth('ALK', 2.8) - 1e-9,
          (math.hypot(ux, uy), layout.tabTextWidth('ALK', 2.8)))

# The check above measures the text band against the hypotenuse. That is not
# where the lettering escaped: with the width underestimated, the ends of the
# text ran out past the LEGS, which are buried in the bin walls, and the last
# letter surfaced inside the wall. Sum-of-distances hides that - a point past a
# leg still sums to less than the leg length - so resolve the band into the
# triangle's own axes and check all three edges separately, for every code in
# the table, at the height that actually ships.
for (_chem, code) in batteryDefs.CHEMISTRY_LABELS:
    if not code:
        continue
    height = batteryDefs.DEFAULT_TAB_TEXT_HEIGHT
    margin = batteryDefs.DEFAULT_TAB_MARGIN
    leg = layout.tabLegForText(code, height, margin)
    for corner in layout.TAB_CORNERS:
        cornerPt, legA, legB = layout.tabTriangle(fw, fl, leg, corner)
        axisA = ((legA[0] - cornerPt[0]) / leg, (legA[1] - cornerPt[1]) / leg)
        axisB = ((legB[0] - cornerPt[0]) / leg, (legB[1] - cornerPt[1]) / leg)
        (sx, sy), (ex, ey) = layout.tabTextBaseline(fw, fl, leg, margin, corner)
        midX = (legA[0] + legB[0]) / 2.0
        midY = (legA[1] + legB[1]) / 2.0
        inX, inY = cornerPt[0] - midX, cornerPt[1] - midY
        inLen = math.hypot(inX, inY)
        inX, inY = inX / inLen, inY / inLen
        ux, uy = ex - sx, ey - sy
        runLen = math.hypot(ux, uy)
        dirX, dirY = ux / runLen, uy / runLen
        midBaseX, midBaseY = (sx + ex) / 2.0, (sy + ey) / 2.0
        half = layout.tabTextWidth(code, height) / 2.0
        insideWalls = insideHyp = True
        for along in (-half, half):
            for deep in (0.0, height):
                px = midBaseX + dirX * along + inX * deep - cornerPt[0]
                py = midBaseY + dirY * along + inY * deep - cornerPt[1]
                a = px * axisA[0] + py * axisA[1]
                b = px * axisB[0] + py * axisB[1]
                insideWalls = insideWalls and a >= -1e-9 and b >= -1e-9
                insideHyp = insideHyp and a + b <= leg + 1e-9
        check('{} in the {} corner clears both walls'.format(code, corner.lower()),
              insideWalls)
        check('{} in the {} corner clears the hypotenuse'.format(code, corner.lower()),
              insideHyp)

# and the estimate the shelf is cut from has to match the font it is set in
check('ALK at 7.5 mm is 22.4 mm of Arial Bold, not 15.3',
      abs(layout.tabTextWidth('ALK', 7.5) - 22.41) < 0.05,
      layout.tabTextWidth('ALK', 7.5))

print('--- lettering stroke width ---')
# raised text prints as walls, so a stem thinner than the extrusion width is
# not thinned, it is discarded - and the label vanishes with no warning
check('stem scales with height',
      abs(layout.tabStemWidth(2.8) - 2.8 * layout.STEM_RATIO) < 1e-9)
check('the default height clears a 0.4 mm nozzle',
      layout.tabStemWidth(batteryDefs.DEFAULT_TAB_TEXT_HEIGHT)
      >= batteryDefs.MIN_PRINTABLE_STROKE,
      layout.tabStemWidth(batteryDefs.DEFAULT_TAB_TEXT_HEIGHT))
check('half that height does not', layout.tabStemWidth(1.4) < batteryDefs.MIN_PRINTABLE_STROKE)
# the default is sized for legibility, not for costing nothing
check('the default lettering is well clear of the nozzle limit',
      layout.tabStemWidth(batteryDefs.DEFAULT_TAB_TEXT_HEIGHT)
      > 2 * batteryDefs.MIN_PRINTABLE_STROKE,
      layout.tabStemWidth(batteryDefs.DEFAULT_TAB_TEXT_HEIGHT))

print('--- the one-slot shelf size ---')
# 18 mm is the largest corner shelf that never costs more than a single slot,
# and never the last one. This is measured, so it is asserted rather than
# trusted: exhaustively at the limit, and shown to break just past it.
def shelfCost(leg):
    worstBlocked = 0
    emptied = False
    for bat in batteryDefs.BATTERY_TYPES:
        d = batteryDefs.BATTERY_DEFAULTS[bat]
        for bx in range(1, 6):
            for by in range(1, 6):
                if (bx, by) == (1, 1):
                    continue  # a one-battery bin is not a thing anyone prints
                fw, fl = floorDims(bx, by)
                if d['isRound']:
                    res = layout.computeRoundLayout(fw, fl, d['slotDiaLen'], 3.0, 5.0)
                else:
                    res = layout.computeRectLayout(fw, fl, d['slotDiaLen'],
                                                   d['slotWidth'], 3.0, 5.0)
                if res is None or leg >= min(fw, fl):
                    continue
                for corner in layout.TAB_CORNERS:
                    trimmed = layout.removeSlotsUnderTab(
                        res, layout.tabTriangle(fw, fl, leg, corner))
                    if trimmed is None or trimmed['count'] < 1:
                        emptied = True
                        continue
                    worstBlocked = max(worstBlocked, trimmed['blocked'])
    return worstBlocked, emptied

blocked, emptied = shelfCost(batteryDefs.ONE_SLOT_TAB_LEG)
print('an {} mm shelf costs at most {} slot(s)'.format(batteryDefs.ONE_SLOT_TAB_LEG, blocked))
check('the one-slot shelf costs at most one slot', blocked <= 1, blocked)
check('the one-slot shelf never empties a bin', not emptied)
overBlocked, overEmptied = shelfCost(batteryDefs.ONE_SLOT_TAB_LEG + 0.5)
check('half a millimetre more does empty one', overEmptied or overBlocked > 1,
      (overBlocked, overEmptied))

# the shipped default has to sit inside that ceiling, and print
defaultLeg = layout.tabLegForText('ALK', batteryDefs.DEFAULT_TAB_TEXT_HEIGHT,
                                  batteryDefs.DEFAULT_TAB_MARGIN)
check('the default shelf is within the one-slot size',
      defaultLeg <= batteryDefs.ONE_SLOT_TAB_LEG, defaultLeg)
check('the default lettering prints',
      layout.tabStemWidth(batteryDefs.DEFAULT_TAB_TEXT_HEIGHT)
      >= batteryDefs.MIN_PRINTABLE_STROKE)
# every code in the table has to fit the one-slot shelf at the shipped height,
# and the widest of them is what sets that height
for (_name, code) in batteryDefs.CHEMISTRY_LABELS:
    if not code:
        continue
    leg = layout.tabLegForText(code, batteryDefs.DEFAULT_TAB_TEXT_HEIGHT,
                               batteryDefs.DEFAULT_TAB_MARGIN)
    check(code + ' fits the one-slot shelf at the default height',
          leg <= batteryDefs.ONE_SLOT_TAB_LEG, leg)
# A free shelf - one provably too small to touch a slot - holds a two-letter
# code at a printable size, but not a three-letter one: the widths that fixed
# the overrun also shrank what 10 mm of leg will carry.
freeTwo = layout.tabTextHeightForLeg(layout.freeTabLeg(5.0), 'LI',
                                     batteryDefs.DEFAULT_TAB_MARGIN)
check('a free shelf prints a two-letter code',
      layout.tabStemWidth(freeTwo) >= batteryDefs.MIN_PRINTABLE_STROKE, freeTwo)
freeThree = layout.tabTextHeightForLeg(layout.freeTabLeg(5.0), 'ALK',
                                       batteryDefs.DEFAULT_TAB_MARGIN)
check('a free shelf cannot print three letters, and the dialog says so',
      layout.tabStemWidth(freeThree) < batteryDefs.MIN_PRINTABLE_STROKE, freeThree)

print('--- shelf corner against the bin fillet ---')
# the shelf overlaps the wall for a clean join, but a square corner pushed too
# far lands outside the bin's filleted outer corner and hangs off the edge
for (outerFillet, wall) in ((3.75, 2.15), (3.75, 1.6), (3.75, 3.0), (3.5, 2.15)):
    limit = layout.cornerBuryLimit(outerFillet, wall)
    inner = max(outerFillet - wall, 0.0)
    check('bury limit {}/{} is positive'.format(outerFillet, wall), limit > 0, limit)
    # exactly at the limit the corner touches the fillet
    check('bury limit {}/{} touches the fillet'.format(outerFillet, wall),
          abs(math.hypot(limit + inner, limit + inner) - outerFillet) < 1e-9)
    # a hair beyond it, the corner is outside
    over = limit + 0.01
    check('past the limit {}/{} the corner is outside'.format(outerFillet, wall),
          math.hypot(over + inner, over + inner) > outerFillet)

# a thin wall leaves the corner outside however little is buried, which the
# generator warns about rather than building silently
check('a thin wall has no safe bury', layout.cornerBuryLimit(3.75, 0.8) < 0,
      layout.cornerBuryLimit(3.75, 0.8))
check('a thick wall has plenty', layout.cornerBuryLimit(3.75, 3.75) > 2.6,
      layout.cornerBuryLimit(3.75, 3.75))

print('--- layer rounding ---')
check('snapUp rounds up', abs(layout.snapUp(43.5, 0.2) - 43.6) < 1e-9, layout.snapUp(43.5, 0.2))
check('snapUp leaves an exact multiple alone',
      abs(layout.snapUp(59.0, 0.2) - 59.0) < 1e-9, layout.snapUp(59.0, 0.2))
check('snapUp with no step is a no-op', layout.snapUp(43.5, 0) == 43.5)
check('snapUp handles float dust',
      abs(layout.snapUp(0.1 + 0.2, 0.1) - 0.3) < 1e-9, layout.snapUp(0.1 + 0.2, 0.1))
check('isMultipleOf true', layout.isMultipleOf(59.0, 0.2))
check('isMultipleOf false', not layout.isMultipleOf(59.5, 0.2))
check('isMultipleOf with no step is vacuously true', layout.isMultipleOf(59.5, 0))

for bat in batteryDefs.BATTERY_TYPES:
    d = batteryDefs.BATTERY_DEFAULTS[bat]
    exact = layout.totalHeight(layout.unitsForWallTop(layout.minWallTop(
        d['ledgeDrop'], d['slotDepth'], d['tipDepth'],
        batteryDefs.DEFAULT_MIN_FLOOR_THICKNESS)))
    for layer in (0.1, 0.15, 0.2, 0.25, 0.28, 0.3):
        snapped = layout.snapUp(exact, layer)
        u = layout.unitsForTotalHeight(snapped)
        # the round trip through unit counts must not lose the layer boundary
        check('{} {}mm layer round trip'.format(bat, layer),
              abs(layout.totalHeight(u) - snapped) < 1e-9,
              (layout.totalHeight(u), snapped))
        check('{} {}mm layer is a whole layer'.format(bat, layer),
              layout.isMultipleOf(layout.totalHeight(u), layer), layout.totalHeight(u))
        check('{} {}mm layer only ever adds height'.format(bat, layer),
              -1e-9 <= snapped - exact < layer, (snapped, exact))
        # the extra height goes into the walls, so the floor can only get thicker
        fc = layout.fitCheck(u, d['ledgeDrop'], d['slotDepth'], d['tipDepth'],
                             d['batteryLength'], batteryDefs.DEFAULT_HEADROOM)
        check('{} {}mm layer keeps the floor'.format(bat, layer),
              fc['floorThickness'] >= batteryDefs.DEFAULT_MIN_FLOOR_THICKNESS - 1e-6,
              fc['floorThickness'])
        check('{} {}mm layer stays stackable'.format(bat, layer), fc['margin'] >= -1e-6)

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

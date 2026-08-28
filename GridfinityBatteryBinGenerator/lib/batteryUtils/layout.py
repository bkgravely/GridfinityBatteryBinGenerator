# Pure geometry/packing math for the GridfinityBatteryBinGenerator add-in.
#
# This module deliberately has NO Fusion 360 (adsk) imports so it can be
# unit-tested with a plain Python interpreter.
#
# All dimensions are millimeters. Coordinates returned are relative to the
# lower-left inside corner of the bin's floor area (the pocket), x across
# the bin width, y across the bin length.

import math

EPS = 1e-6


def _centered(floorW, floorL, centers, count, desc):
    """Shift a list of slot centers so the pattern bounding box is centered
    on the floor area."""
    xs = [c[0] for c in centers]
    ys = [c[1] for c in centers]
    cx = (min(xs) + max(xs)) / 2.0
    cy = (min(ys) + max(ys)) / 2.0
    dx = floorW / 2.0 - cx
    dy = floorL / 2.0 - cy
    return {
        'count': count,
        'centers': [(x + dx, y + dy) for (x, y) in centers],
        'desc': desc,
    }


def _hexCandidate(availA, availB, p):
    """Hex-offset packing with rows running along axis A, stacked along B.
    Returns (count, centers-in-(a,b)-coords, rows, nFull, nOff)."""
    rowPitch = p * math.sqrt(3.0) / 2.0
    nRows = int((availB + EPS) // rowPitch) + 1
    nFull = int((availA + EPS) // p) + 1
    # offset rows are shifted by p/2; do they still fit nFull?
    nOff = nFull if (nFull - 1) * p + p / 2.0 <= availA + EPS else max(nFull - 1, 0)
    count = ((nRows + 1) // 2) * nFull + (nRows // 2) * nOff
    centers = []
    for r in range(nRows):
        shift = 0.0 if r % 2 == 0 else p / 2.0
        n = nFull if r % 2 == 0 else nOff
        for i in range(n):
            centers.append((shift + i * p, r * rowPitch))
    return count, centers, nRows, nFull, nOff


def computeRoundLayout(floorW, floorL, dia, spacing, wallClear):
    """Best packing of circles of diameter `dia` on a floorW x floorL floor.

    Tries a square grid and both orientations of hex-offset packing, keeping
    at least `spacing` between slot edges (including diagonal neighbours in
    the hex pattern, guaranteed because every neighbour center distance is
    exactly the pitch) and `wallClear` between slot edges and the walls.

    Returns dict(count, centers, desc) or None if not even one slot fits.
    """
    p = dia + spacing
    availW = floorW - 2.0 * wallClear - dia
    availL = floorL - 2.0 * wallClear - dia
    if availW < -EPS or availL < -EPS:
        return None
    availW = max(availW, 0.0)
    availL = max(availL, 0.0)

    candidates = []

    # square grid
    nx = int((availW + EPS) // p) + 1
    ny = int((availL + EPS) // p) + 1
    centers = [(i * p, j * p) for j in range(ny) for i in range(nx)]
    candidates.append((nx * ny, centers, 'square grid {}x{}'.format(nx, ny)))

    # hex, rows along X
    count, hcenters, nRows, nFull, nOff = _hexCandidate(availW, availL, p)
    candidates.append((
        count,
        [(a, b) for (a, b) in hcenters],
        'hex offset, {} rows of {}/{}'.format(nRows, nFull, nOff),
    ))

    # hex, rows along Y
    count, hcenters, nRows, nFull, nOff = _hexCandidate(availL, availW, p)
    candidates.append((
        count,
        [(b, a) for (a, b) in hcenters],
        'hex offset (rotated), {} columns of {}/{}'.format(nRows, nFull, nOff),
    ))

    best = max(candidates, key=lambda c: c[0])
    if best[0] <= 0:
        return None
    return _centered(floorW, floorL, best[1], best[0], best[2])


def _rectGrid(availW, availL, sx, sy, spacing):
    """Pack sx-by-sy rectangles into an availW x availL area, corner-anchored.

    Returns dict(count, centers, usedW, usedL, nx, ny) or None if none fit.
    Centers are measured from the corner of the available area.
    """
    if availW < sx - EPS or availL < sy - EPS:
        return None
    px, py = sx + spacing, sy + spacing
    nx = int((availW - sx + EPS) // px) + 1
    ny = int((availL - sy + EPS) // py) + 1
    return {
        'count': nx * ny,
        'centers': [(i * px + sx / 2.0, j * py + sy / 2.0)
                    for j in range(ny) for i in range(nx)],
        'usedW': nx * sx + (nx - 1) * spacing,
        'usedL': ny * sy + (ny - 1) * spacing,
        'nx': nx, 'ny': ny,
    }


def computeRectLayout(floorW, floorL, slotL, slotW, spacing, wallClear,
                      allowMixed=True):
    """Best packing of slotL x slotW rectangles on the floor area.

    Tries the slot both ways round and, with `allowMixed`, mixed layouts too:
    a main block in one orientation plus a leftover strip in the other, along
    the side or the top. A 9V slot is far from square, so the offcut left by a
    uniform grid is often wide enough for a row turned the other way - a 3x3
    bin fits 18 that way against 15 uniform.

    With `allowMixed` off, every slot in the bin faces the same way: fewer
    batteries, but a tidier bin that is easier to load without looking.

    Returns dict(count, centers, slotSizes, desc) with slotSizes parallel to
    centers as (width, length) per slot, or None if nothing fits.
    """
    availW = floorW - 2.0 * wallClear
    availL = floorL - 2.0 * wallClear
    best = None

    def consider(slots, desc):
        nonlocal best
        if slots and (best is None or len(slots) > len(best[0])):
            best = (slots, desc)

    for (sx, sy, tag) in ((slotL, slotW, 'flat'), (slotW, slotL, 'upright')):
        main = _rectGrid(availW, availL, sx, sy, spacing)
        if main is None:
            continue
        mainSlots = [(cx, cy, sx, sy) for (cx, cy) in main['centers']]
        consider(mainSlots, '{} {}x{}'.format(tag, main['nx'], main['ny']))
        if not allowMixed:
            continue

        # the same rectangles turned 90 degrees, for whatever space is left over
        ox, oy = sy, sx
        side = _rectGrid(availW - main['usedW'] - spacing, availL, ox, oy, spacing)
        if side:
            offset = main['usedW'] + spacing
            consider(mainSlots + [(cx + offset, cy, ox, oy) for (cx, cy) in side['centers']],
                     '{} {}x{} plus {} turned along the side'.format(
                         tag, main['nx'], main['ny'], side['count']))
        top = _rectGrid(availW, availL - main['usedL'] - spacing, ox, oy, spacing)
        if top:
            offset = main['usedL'] + spacing
            consider(mainSlots + [(cx, cy + offset, ox, oy) for (cx, cy) in top['centers']],
                     '{} {}x{} plus {} turned along the end'.format(
                         tag, main['nx'], main['ny'], top['count']))

    if best is None:
        return None

    slots, desc = best
    # centre the whole arrangement, mixed orientations included, on the floor
    minX = min(x - w / 2.0 for (x, y, w, l) in slots)
    maxX = max(x + w / 2.0 for (x, y, w, l) in slots)
    minY = min(y - l / 2.0 for (x, y, w, l) in slots)
    maxY = max(y + l / 2.0 for (x, y, w, l) in slots)
    dx = floorW / 2.0 - (minX + maxX) / 2.0
    dy = floorL / 2.0 - (minY + maxY) / 2.0
    return {
        'count': len(slots),
        'centers': [(x + dx, y + dy) for (x, y, w, l) in slots],
        'slotSizes': [(w, l) for (x, y, w, l) in slots],
        'desc': desc,
    }


def bodyTopHeight(heightUnits, heightUnitMm=7.0, baseHeightMm=5.0):
    """Height of the top face of the bin walls (where the stacking lip
    begins) above the bottom of the FULL bin body (top of the base studs),
    matching the GridfinityGenerator formula:
    (u - 1) * unit + max(0, unit - baseHeight)."""
    return (heightUnits - 1) * heightUnitMm + max(0.0, heightUnitMm - baseHeightMm)


def minWallTop(ledgeDrop, slotDepth, tipDepth, minFloor=1.0):
    """Exact wall-top height the cuts require, in mm and not rounded up to a
    height unit. Only the floor rule constrains it: the stackability check
    depends on ledge drop and slot depth, which move with the wall top."""
    return ledgeDrop + slotDepth + tipDepth + minFloor


def unitsForWallTop(wallTop, heightUnitMm=7.0, baseHeightMm=5.0):
    """Height in gridfinity units - fractional is fine - giving that wall top.

    Gridfinity only fixes the 42 mm footprint; height is free. The bin body
    generator takes a unit count as a real number, so a bin can be exactly as
    tall as its contents need rather than rounded up to the next 7 mm.
    """
    lipUnderBase = max(0.0, heightUnitMm - baseHeightMm)
    return (wallTop - lipUnderBase) / heightUnitMm + 1.0


def totalHeight(units, heightUnitMm=7.0, baseHeightMm=5.0):
    """Overall printed height of the bin, base included."""
    return bodyTopHeight(units, heightUnitMm, baseHeightMm) + baseHeightMm


def unitsForTotalHeight(total, heightUnitMm=7.0, baseHeightMm=5.0):
    """Inverse of totalHeight: unit count (fractional) for an overall height."""
    return unitsForWallTop(total - baseHeightMm, heightUnitMm, baseHeightMm)


def snapUp(value, step):
    """Round `value` up to the next whole multiple of `step`.

    Used to land the top of a free-height bin on a layer boundary: a bin that
    is 54.5 mm tall printed at 0.2 mm layers ends mid-layer, and the slicer
    either drops the last layer or squashes it. A step of 0 (or None) leaves
    the value alone.
    """
    if not step or step <= EPS:
        return value
    return math.ceil(value / step - EPS) * step


def isMultipleOf(value, step):
    """True if `value` is a whole number of `step`s (within tolerance)."""
    if not step or step <= EPS:
        return True
    return abs(value / step - round(value / step)) < 1e-6


def autoMinHeightUnits(ledgeDrop, slotDepth, tipDepth, minFloor=1.0,
                       heightUnitMm=7.0, baseHeightMm=5.0):
    """Smallest whole number of gridfinity height units that still leaves a
    solid floor of at least `minFloor` beneath the deepest cut.

    The cut must not reach the underside of the bin body at all. The feet
    cover only part of that face, so anything dipping below it breaks clean
    through wherever a slot lands over the gap between two feet - and the
    slot grid is centred on the bin, not aligned to the 42 mm foot pitch, so
    which slots line up with a gap is pure chance.
    """
    deepestCut = ledgeDrop + slotDepth + tipDepth + minFloor
    lipUnderBase = max(0.0, heightUnitMm - baseHeightMm)
    # wallTop(u) = (u - 1) * heightUnitMm + lipUnderBase  >=  deepestCut
    u = math.ceil((deepestCut - lipUnderBase) / heightUnitMm - EPS) + 1
    return max(u, 1)


def fitCheck(heightUnits, ledgeDrop, slotDepth, tipDepth, batteryLength,
             headroom, heightUnitMm=7.0, baseHeightMm=5.0):
    """Stackability + feasibility check. The battery is treated as resting
    with its full overall length above the slot bottom (as if the button
    carried it) - the conservative case.

    Returns dict with:
      margin        >= 0 means battery top stays at least `headroom` below
                    the wall top. Note this is independent of heightUnits
                    because the ledge is measured as a drop from the wall
                    top; the fix for a negative margin is a deeper slot or
                    bigger ledge drop.
      floorThickness
                    solid material left under the deepest cut, measured to
                    the underside of the bin body. Must stay positive: the
                    feet do not cover that whole face, so anything at or
                    below zero breaks through between them. Fixed by adding
                    height units.
      wallTop, ledgeZ, slotBottomZ, recessBottomZ, batteryTop
                    heights above the bin body bottom (top of base studs).
    """
    wallTop = bodyTopHeight(heightUnits, heightUnitMm, baseHeightMm)
    ledgeZ = wallTop - ledgeDrop
    slotBottomZ = ledgeZ - slotDepth
    recessBottomZ = slotBottomZ - tipDepth
    batteryTop = slotBottomZ + batteryLength
    margin = wallTop - headroom - batteryTop
    return {
        'wallTop': wallTop,
        'ledgeZ': ledgeZ,
        'slotBottomZ': slotBottomZ,
        'recessBottomZ': recessBottomZ,
        'batteryTop': batteryTop,
        'margin': margin,
        'floorThickness': recessBottomZ,
        'neededExtraDrop': max(0.0, -margin),
    }


def minDistance(centers):
    """Smallest center-to-center distance in a layout (for tests)."""
    m = None
    for i in range(len(centers)):
        for j in range(i + 1, len(centers)):
            d = math.hypot(centers[i][0] - centers[j][0],
                           centers[i][1] - centers[j][1])
            if m is None or d < m:
                m = d
    return m

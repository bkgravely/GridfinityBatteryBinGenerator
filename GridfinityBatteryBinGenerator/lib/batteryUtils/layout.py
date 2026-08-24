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


def computeRectLayout(floorW, floorL, slotL, slotW, spacing, wallClear):
    """Best grid of slotL x slotW rectangles (tries both orientations).

    Returns dict(count, centers, desc, slotX, slotY) where slotX/slotY are
    the chosen slot footprint along x/y, or None if nothing fits.
    """
    best = None
    for (sx, sy, rotated) in ((slotL, slotW, False), (slotW, slotL, True)):
        availW = floorW - 2.0 * wallClear - sx
        availL = floorL - 2.0 * wallClear - sy
        if availW < -EPS or availL < -EPS:
            continue
        availW = max(availW, 0.0)
        availL = max(availL, 0.0)
        px = sx + spacing
        py = sy + spacing
        nx = int((availW + EPS) // px) + 1
        ny = int((availL + EPS) // py) + 1
        count = nx * ny
        if count <= 0:
            continue
        centers = [(i * px, j * py) for j in range(ny) for i in range(nx)]
        desc = 'grid {}x{}{}'.format(nx, ny, ' (rotated 90\N{DEGREE SIGN})' if rotated else '')
        if best is None or count > best[0]:
            best = (count, centers, desc, sx, sy)
    if best is None:
        return None
    result = _centered(floorW, floorL, best[1], best[0], best[2])
    result['slotX'] = best[3]
    result['slotY'] = best[4]
    return result


def bodyTopHeight(heightUnits, heightUnitMm=7.0, baseHeightMm=5.0):
    """Height of the top face of the bin walls (where the stacking lip
    begins) above the bottom of the FULL bin body (top of the base studs),
    matching the GridfinityGenerator formula:
    (u - 1) * unit + max(0, unit - baseHeight)."""
    return (heightUnits - 1) * heightUnitMm + max(0.0, heightUnitMm - baseHeightMm)


def autoMinHeightUnits(ledgeDrop, slotDepth, tipDepth, baseDipAllowance=0.5,
                       heightUnitMm=7.0, baseHeightMm=5.0):
    """Smallest whole number of gridfinity height units such that the deepest
    cut (slot + tip recess, measured `ledgeDrop + slotDepth + tipDepth` below
    the wall top) stays inside the bin body, allowing it to dip at most
    `baseDipAllowance` below the body bottom into the solid base studs."""
    deepestCut = ledgeDrop + slotDepth + tipDepth - baseDipAllowance
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
      baseDip       how far the deepest cut (tip recess bottom) extends
                    below the bin body into the base studs (0 if it stays
                    inside the body). Fixed by adding height units.
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
        'baseDip': max(0.0, -recessBottomZ),
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

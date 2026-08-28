# Logo engraving helpers for the BatteryBinGenerator add-in.
#
# Pure Python (no Fusion/adsk imports) so the geometry maths and the SVG
# rewriting can be unit-tested outside Fusion.
#
# The logo is engraved into the flat bottom face of a gridfinity foot - the
# only surface on the underside that prints flat against the build plate.
# It must be recessed, never raised: a raised mark would hold the bin off
# the plate and make it rock on a baseplate.
#
# All dimensions in millimeters.

import math
import os
import re

# gridfinity base profile, mm (mirrors lib/gridfinityUtils/const.py, which is cm)
BASE_TOP_CHAMFER = 2.4     # 45 deg, so it insets the profile by the same amount
BASE_MID_HEIGHT = 1.8
BASE_BOTTOM_CHAMFER = 0.8  # 45 deg
BASE_HEIGHT = BASE_TOP_CHAMFER + BASE_MID_HEIGHT + BASE_BOTTOM_CHAMFER  # 5.0

PLACEMENT_CORNER = 'Corner foot'
PLACEMENT_CENTER = 'Center foot'
PLACEMENT_EVERY = 'Every foot'
PLACEMENTS = [PLACEMENT_CORNER, PLACEMENT_CENTER, PLACEMENT_EVERY]

DEFAULT_FOOT_MARGIN = 2.0     # keep the logo clear of the foot's bottom chamfer

# --------------------------------------------------------------- fixed settings
# The logo is deliberately not a dialog option - every bin carries it. This is
# the only place it is configured.
# A foot offers 35.1 mm of flat face, so 31.1 mm is the ceiling with the 2 mm
# margin above. Sized right at it: at 28 mm the thinnest glyph in the wordmark
# (the S) engraved a groove too narrow to survive slicing, and the letter was
# lost on the print.
LOGO_SIZE = 31.0                    # mm across the artwork's largest dimension
LOGO_DEPTH = 0.4                    # mm, two 0.2 mm layers
LOGO_PLACEMENT = PLACEMENT_CORNER   # which foot carries the mark
# The bundled artwork is already mirrored AND rotated in its path data, so
# no runtime transform is needed. These apply to artwork swapped in later.
LOGO_MIRROR = False
LOGO_ROTATION = 0                   # 0/90/180/270


def footFlatWidth(baseWidth, xyClearance,
                  topChamfer=BASE_TOP_CHAMFER, bottomChamfer=BASE_BOTTOM_CHAMFER):
    """Width of the flat bottom face of one gridfinity foot.

    The foot's footprint is the grid pitch less the xy clearance on both
    sides; the 45 degree top and bottom chamfers each inset it further by
    their own height. For stock values (42 pitch, 0.25 clearance) this is
    41.5 - 4.8 - 1.6 = 35.1 mm.
    """
    return baseWidth - 2.0 * xyClearance - 2.0 * topChamfer - 2.0 * bottomChamfer


def maxLogoWidth(baseWidth, xyClearance, margin=DEFAULT_FOOT_MARGIN):
    """Largest logo that still leaves `margin` of flat face all round."""
    return max(0.0, footFlatWidth(baseWidth, xyClearance) - 2.0 * margin)


def footCenter(i, j, baseWidth, baseLength, xyClearance):
    """Center of foot (i, j) in the bin component's model coordinates.

    Foot i spans x from i*baseWidth to i*baseWidth + (baseWidth - 2*clearance),
    matching how baseGenerator lays out the pattern and trims the clearance.
    """
    return (i * baseWidth + (baseWidth - 2.0 * xyClearance) / 2.0,
            j * baseLength + (baseLength - 2.0 * xyClearance) / 2.0)


def footCenters(binX, binY, baseWidth, baseLength, xyClearance, placement):
    """Centers of every foot that should receive a logo, in model mm."""
    if placement == PLACEMENT_EVERY:
        return [footCenter(i, j, baseWidth, baseLength, xyClearance)
                for j in range(binY) for i in range(binX)]
    if placement == PLACEMENT_CENTER:
        # for an even count there is no true middle; take the lower-left of
        # the two middle feet so the choice is deterministic
        return [footCenter((binX - 1) // 2, (binY - 1) // 2,
                           baseWidth, baseLength, xyClearance)]
    return [footCenter(0, 0, baseWidth, baseLength, xyClearance)]


def bottomZ(baseHeight=BASE_HEIGHT):
    """Z of the printed bottom face. The bin body starts at z=0 and the base
    is extruded downwards from there, so the feet bottom out at -baseHeight."""
    return -baseHeight


# ------------------------------------------------------------ profile nesting
#
# An imported logo yields one sketch profile per enclosed region, so a letter
# "O" gives both the ring AND the disc inside it. Cutting every profile would
# fill the counters in and turn the O into a blob. Regions alternate as you
# nest inwards - engrave, hole, engrave - so keeping only even nesting depths
# reproduces what the artwork looks like, including islands inside counters.


def _boxContains(outer, inner, tol=1e-6):
    return (outer[0] <= inner[0] + tol and outer[1] <= inner[1] + tol
            and outer[2] >= inner[2] - tol and outer[3] >= inner[3] - tol)


def _boxArea(box):
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])


def keepByNestingParity(boxes, tol=1e-6):
    """Indices of the regions to cut, given each region's bounding box.

    A region nested inside an odd number of others is a hole and is skipped;
    everything else is engraved. Boxes are (minX, minY, maxX, maxY).
    """
    keep = []
    for i, box in enumerate(boxes):
        depth = 0
        for j, other in enumerate(boxes):
            if i == j:
                continue
            if _boxContains(other, box, tol) and _boxArea(other) > _boxArea(box) + tol:
                depth += 1
        if depth % 2 == 0:
            keep.append(i)
    return keep


# --------------------------------------------------------------- SVG rewriting
#
# Mirroring matters: the sketch is drawn on a plane whose normal points up
# into the bin, so when you turn the bin over and look at the underside you
# see it reversed. Mirroring the source makes it read correctly in the hand.
#
# Fusion imports SVG geometry as FIXED curves, so nothing can be moved,
# rotated or mirrored after the fact - Sketch.move just quietly does nothing.
# Orientation therefore has to be in the file before it is imported. The
# bundled artwork already has it baked into its path data, which is the most
# reliable form; these helpers wrap a transform around the content instead,
# for artwork swapped in later. Any offset the transform introduces is
# irrelevant because the import is re-centred on the foot anyway.

_SVG_OPEN = re.compile(r'<\s*svg\b', re.IGNORECASE)


def _openTagEnd(svgText, start):
    """Index just past the '>' of the tag starting at `start`, honouring
    quoted attribute values so a '>' inside an attribute doesn't fool us."""
    quote = None
    i = start
    while i < len(svgText):
        ch = svgText[i]
        if quote:
            if ch == quote:
                quote = None
        elif ch in '"\'':
            quote = ch
        elif ch == '>':
            return i + 1
        i += 1
    return -1


def svgTransformAttr(mirror, rotationDeg):
    """SVG transform string for the requested orientation, or '' for none."""
    parts = []
    rotationDeg = int(rotationDeg) % 360
    if rotationDeg:
        parts.append('rotate({})'.format(rotationDeg))
    if mirror:
        parts.append('scale(-1,1)')
    return ' '.join(parts)


_VIEWBOX_RE = re.compile(r'viewBox\s*=\s*"([^"]*)"', re.IGNORECASE)
_SIZE_RE = re.compile(r'\s(?:width|height)\s*=\s*"[^"]*"', re.IGNORECASE)


def transformedViewBox(viewBox, mirror, rotationDeg):
    """The viewBox that still contains the artwork once transformed.

    Rotating about the origin walks the artwork straight out of the original
    viewBox, and importers clip to it - which is how a rotated logo silently
    becomes no logo at all. Returns None if the viewBox can't be parsed.
    """
    parts = viewBox.replace(',', ' ').split()
    if len(parts) != 4:
        return None
    try:
        minX, minY, width, height = [float(value) for value in parts]
    except ValueError:
        return None

    angle = math.radians(int(rotationDeg) % 360)
    cosA, sinA = math.cos(angle), math.sin(angle)
    xs, ys = [], []
    for (x, y) in ((minX, minY), (minX + width, minY),
                   (minX, minY + height), (minX + width, minY + height)):
        # transform="rotate() scale()" applies right to left, so mirror first
        if mirror:
            x = -x
        xs.append(x * cosA - y * sinA)
        ys.append(x * sinA + y * cosA)
    return '{:.4f} {:.4f} {:.4f} {:.4f}'.format(
        min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))


def wrapSvgTransform(svgText, mirror=False, rotationDeg=0):
    """Wrap the SVG's content in a <g> carrying the mirror/rotation transform.

    The viewBox is widened to match, and any width/height attributes are
    dropped so they cannot squash the result into the old aspect ratio.

    Returns the original text unchanged when no transform is needed. Raises
    ValueError if the text has no usable <svg> element.
    """
    transform = svgTransformAttr(mirror, rotationDeg)
    if not transform:
        return svgText

    match = _SVG_OPEN.search(svgText)
    if not match:
        raise ValueError('No <svg> element found in the logo file.')
    openEnd = _openTagEnd(svgText, match.start())
    if openEnd < 0:
        raise ValueError('Malformed <svg> tag in the logo file.')
    if svgText[:openEnd].rstrip().endswith('/>'):
        raise ValueError('The logo file has an empty <svg> element.')
    closeStart = svgText.upper().rfind('</SVG')
    if closeStart < 0 or closeStart < openEnd:
        raise ValueError('No closing </svg> tag in the logo file.')

    openTag = svgText[match.start():openEnd]
    viewBox = _VIEWBOX_RE.search(openTag)
    if viewBox:
        newBox = transformedViewBox(viewBox.group(1), mirror, rotationDeg)
        if newBox:
            openTag = _SIZE_RE.sub('', openTag)
            openTag = _VIEWBOX_RE.sub('viewBox="{}"'.format(newBox), openTag, count=1)

    return (svgText[:match.start()]
            + openTag
            + '<g transform="' + transform + '">'
            + svgText[openEnd:closeStart]
            + '</g>'
            + svgText[closeStart:])


def orientedSvgPath(srcPath, mirror, rotationDeg, tempDir):
    """Path of an SVG with the requested orientation baked in.

    Returns srcPath untouched when no transform is needed, otherwise writes a
    rewritten copy into tempDir under a deterministic name and returns that.
    The copy is left in place: Fusion may re-read the file when the timeline
    is rolled, so deleting it immediately would be unsafe.
    """
    if not svgTransformAttr(mirror, rotationDeg):
        return srcPath
    with open(srcPath, 'r', encoding='utf-8') as handle:
        text = handle.read()
    rewritten = wrapSvgTransform(text, mirror, rotationDeg)
    stem = os.path.splitext(os.path.basename(srcPath))[0]
    name = '{}_m{}_r{}.svg'.format(stem, 1 if mirror else 0, int(rotationDeg) % 360)
    outPath = os.path.join(tempDir, 'GridfinityBatteryBinLogo_' + name)
    with open(outPath, 'w', encoding='utf-8') as handle:
        handle.write(rewritten)
    return outPath

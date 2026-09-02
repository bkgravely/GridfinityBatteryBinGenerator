# Bake the engraving orientation into a logo SVG's path data.
#
#   python3 tools/bake_logo.py SOURCE.svg OUTPUT.svg
#
# Fusion imports SVG geometry as fixed curves and clips to the viewBox, so a
# transform attribute on a <g> is not something to rely on: the artwork either
# ignores it or lands outside the box and is silently clipped away. This bakes
# the transform into the coordinates instead.
#
# The transform is the one an engraving on the underside of a bin needs:
#   1. mirror about the artwork's own vertical centre line, so it reads the
#      right way round when you turn the bin over, and
#   2. rotate 90 degrees, so it sits upright on the foot.
#
# Two cleanups matter as much as the transform. Zero-length segments (Adobe
# exports are full of them) and contours that do not close exactly on their
# start point both stop Fusion forming a profile, and a region with no profile
# is a region that does not get engraved.

import re
import sys

from svgpathtools import parse_path, Path, Line, CubicBezier, QuadraticBezier, Arc

ROTATION_DEG = 90
MIRROR = True
CLOSE_TOL = 1e-6
# Segments shorter than this (in SVG user units) are dropped as degenerate.
# It is not just about tidiness: Illustrator ends contours with a hairline stub
# a hundredth of a unit long that doubles back over its neighbour, and an
# outline that crosses itself extrudes into a non-manifold edge - which every
# slicer then complains about. The real geometry in this artwork has nothing
# under half a unit, so 0.05 units sits a hundred times below anything meant to
# be there, and comfortably above the stubs and spikes that are not.
DEGENERATE_TOL = 0.05

_PATH_D = re.compile(r'(<path\b[^>]*?\bd\s*=\s*")([^"]*)(")', re.IGNORECASE | re.DOTALL)
_VIEWBOX = re.compile(r'viewBox\s*=\s*"([^"]*)"', re.IGNORECASE)
_SIZE = re.compile(r'\s(?:width|height)\s*=\s*"[^"]*"', re.IGNORECASE)


def viewBoxWidth(svgText):
    match = _VIEWBOX.search(svgText)
    if not match:
        raise ValueError('the source SVG has no viewBox')
    parts = match.group(1).replace(',', ' ').split()
    minX, minY, width, height = [float(v) for v in parts]
    return minX, minY, width, height


def mapPoint(z, width):
    """Mirror about the artwork's centre, then rotate 90 degrees about the
    origin: (x, y) -> (-y, width - x). Complex numbers are how svgpathtools
    carries points, real = x, imag = y."""
    x, y = z.real, z.imag
    if MIRROR:
        x = width - x
    if ROTATION_DEG % 360 == 90:
        return complex(-y, x)
    if ROTATION_DEG % 360 == 0:
        return complex(x, y)
    raise ValueError('only 0 and 90 degree rotations are baked here')


def mapSegment(seg, width):
    m = lambda z: mapPoint(z, width)
    if isinstance(seg, Line):
        return Line(m(seg.start), m(seg.end))
    if isinstance(seg, CubicBezier):
        return CubicBezier(m(seg.start), m(seg.control1), m(seg.control2), m(seg.end))
    if isinstance(seg, QuadraticBezier):
        return QuadraticBezier(m(seg.start), m(seg.control), m(seg.end))
    if isinstance(seg, Arc):
        # an arc under a mirror flips sweep; rotation just moves the axis angle
        rotation = seg.rotation + (ROTATION_DEG if not MIRROR else -ROTATION_DEG)
        return Arc(m(seg.start), seg.radius, rotation,
                   seg.large_arc, not seg.sweep if MIRROR else seg.sweep, m(seg.end))
    raise TypeError('unhandled segment type {}'.format(type(seg)))


def withEndpoints(seg, start=None, end=None):
    """The same segment with one or both endpoints moved, control points kept."""
    start = seg.start if start is None else start
    end = seg.end if end is None else end
    if isinstance(seg, Line):
        return Line(start, end)
    if isinstance(seg, CubicBezier):
        return CubicBezier(start, seg.control1, seg.control2, end)
    if isinstance(seg, QuadraticBezier):
        return QuadraticBezier(start, seg.control, end)
    return Arc(start, seg.radius, seg.rotation, seg.large_arc, seg.sweep, end)


def trimOverlappingTail(segs):
    """Cut a contour whose end runs back over its beginning.

    Illustrator likes to close a shape by carrying the last segment past the
    first one instead of meeting it. Snapping the endpoints together leaves
    that overshoot in place as a crossing, which extrudes into a non-manifold
    edge. Where the tail really does cross the head, the honest closure is at
    the crossing itself: keep the part of the first segment after it, the part
    of the crossing segment before it, and throw away everything past.
    """
    n = len(segs)
    for j in range(n - 1, 1, -1):
        hits = segs[0].intersect(segs[j])
        if not hits:
            continue
        t0, tj = hits[0]
        point = segs[0].point(t0)
        head = withEndpoints(segs[0], start=point)
        tail = withEndpoints(segs[j], end=point)
        kept = [head] + segs[1:j] + [tail]
        return [s for s in kept if abs(s.end - s.start) > CLOSE_TOL], n - len(kept)
    return segs, 0


def cleanSubpath(sub):
    """Drop degenerate segments, heal the gaps that leaves, trim any tail that
    overshoots the start, and snap the contour shut."""
    segs = [s for s in sub if abs(s.end - s.start) > DEGENERATE_TOL]
    if not segs:
        return None, 0
    dropped = len(sub) - len(segs)

    # dropping an interior segment leaves a gap; pull the next one back onto
    # the previous endpoint rather than emitting a discontinuous contour
    for k in range(1, len(segs)):
        if abs(segs[k].start - segs[k - 1].end) > CLOSE_TOL:
            segs[k] = withEndpoints(segs[k], start=segs[k - 1].end)

    segs, trimmed = trimOverlappingTail(segs)
    dropped += trimmed
    if abs(segs[-1].end - segs[0].start) > CLOSE_TOL:
        segs[-1] = withEndpoints(segs[-1], end=segs[0].start)
    return Path(*segs), dropped


def bakePathData(d, width, stats):
    out = []
    for sub in parse_path(d).continuous_subpaths():
        moved = Path(*[mapSegment(s, width) for s in sub])
        cleaned, dropped = cleanSubpath(moved)
        stats['dropped'] += dropped
        if cleaned is None:
            stats['empty'] += 1
            continue
        stats['contours'] += 1
        out.append(cleaned.d())
    return ' '.join(out)


_GRAD_OPEN = re.compile(r'<(linear|radial)Gradient\b[^>]*>', re.IGNORECASE)
_GRAD_XFORM = re.compile(r'gradientTransform\s*=\s*"([^"]*)"', re.IGNORECASE)


def _addGradientTransform(svgText, matrix):
    """Prepend `matrix` to every gradient's transform, composing with any the
    artwork already carries rather than emitting a second attribute."""
    def fix(match):
        tag = match.group(0)
        existing = _GRAD_XFORM.search(tag)
        if existing:
            return _GRAD_XFORM.sub(
                'gradientTransform="{} {}"'.format(matrix, existing.group(1)), tag)
        return tag[:-1] + ' gradientTransform="{}">'.format(matrix)
    return _GRAD_OPEN.sub(fix, svgText)


def selfIntersections(sub):
    """Non-adjacent segment pairs of one contour that cross or touch.

    A contour that crosses itself becomes a non-manifold edge once the
    engraving is cut, and slicers refuse to stay quiet about it. Adjacent
    segments are skipped because they legitimately share an endpoint.
    """
    hits = []
    n = len(sub)
    for i in range(n):
        for j in range(i + 1, n):
            if j == i + 1 or (i == 0 and j == n - 1):
                continue
            for (t1, _t2) in sub[i].intersect(sub[j]):
                hits.append((i, j, sub[i].point(t1)))
    return hits


def validate(svgText):
    """Re-parse the baked file and refuse to emit geometry a slicer will flag."""
    problems = []
    shortest = None
    for match in _PATH_D.finditer(svgText):
        for sub in parse_path(match.group(2)).continuous_subpaths():
            for seg in sub:
                length = abs(seg.end - seg.start)
                if shortest is None or length < shortest:
                    shortest = length
            if abs(sub[-1].end - sub[0].start) > CLOSE_TOL:
                problems.append('a contour does not close on its start point')
            for (i, j, point) in selfIntersections(sub):
                problems.append(
                    'a contour crosses itself: segments {} and {} meet at '
                    '({:.3f}, {:.3f})'.format(i, j, point.real, point.imag))
    print('shortest segment {:.4f} units'.format(shortest if shortest else 0.0))
    if problems:
        raise ValueError('baked artwork is not printable:\n  ' + '\n  '.join(problems))
    print('validated: every contour closed, none self-intersecting')


def bake(svgText):
    minX, minY, width, height = viewBoxWidth(svgText)
    if (minX, minY) != (0.0, 0.0):
        raise ValueError('expected a viewBox anchored at the origin')

    stats = {'dropped': 0, 'empty': 0, 'contours': 0}
    bounds = []

    def replace(match):
        baked = bakePathData(match.group(2), width, stats)
        bounds.append(parse_path(baked).bbox())
        return match.group(1) + baked + match.group(3)

    body = _PATH_D.sub(replace, svgText)
    if not stats['contours']:
        raise ValueError('no path data found in the source SVG')

    x0 = min(b[0] for b in bounds); x1 = max(b[1] for b in bounds)
    y0 = min(b[2] for b in bounds); y1 = max(b[3] for b in bounds)
    pad = 2.0
    box = '{:.3f} {:.3f} {:.3f} {:.3f}'.format(
        x0 - pad, y0 - pad, (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad)

    # Gradients are declared in source coordinates, so carry the same mapping
    # over to them or the fill runs the wrong way in a preview. Cosmetic only -
    # Fusion imports geometry and ignores paint - but a file that previews
    # wrongly is a file nobody trusts. (x, y) -> (-y, width - x) as a matrix.
    body = _addGradientTransform(body, 'matrix(0 -1 -1 0 0 {:.4f})'.format(width))

    openTag = re.search(r'<svg\b[^>]*>', body, re.IGNORECASE)
    tag = _SIZE.sub('', openTag.group(0))
    tag = _VIEWBOX.sub('viewBox="{}"'.format(box), tag)
    body = body[:openTag.start()] + tag + body[openTag.end():]

    header = (
        '<!-- Baked by tools/bake_logo.py: mirrored so the engraving reads from\n'
        '     underneath the bin, and rotated {} degrees to sit upright on the\n'
        '     foot. The orientation is in the path data, not a transform\n'
        '     attribute, because Fusion imports SVG geometry as fixed curves\n'
        '     and clips to the viewBox. Do not edit by hand - re-run the tool\n'
        '     against the source artwork instead. -->\n'.format(ROTATION_DEG))
    body = body.replace('<svg', header + '<svg', 1)

    print('contours {contours}, degenerate segments dropped {dropped}, '
          'empty contours skipped {empty}'.format(**stats))
    print('viewBox', box)
    validate(body)
    return body


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__ or 'usage: bake_logo.py SOURCE.svg OUTPUT.svg')
        sys.exit(2)
    with open(sys.argv[1], 'r', encoding='utf-8') as handle:
        text = handle.read()
    # bake first, write second: opening the output truncates it, so doing that
    # before validation leaves an empty logo.svg behind on a failed run
    baked = bake(text)
    with open(sys.argv[2], 'w', encoding='utf-8') as handle:
        handle.write(baked)
    print('wrote', sys.argv[2])

# Battery slot definitions for the GridfinityBatteryBinGenerator add-in.
#
# All linear dimensions are in millimeters. These are the proven values from
# Bryan's manually designed bins and can be edited per-run in the command
# dialog; changing them here changes the defaults offered by the dialog.
#
# Coordinate/height conventions used by the generator:
#   - "heightUnits" is the bin height in gridfinity units (1 u = 7 mm of
#     total bin height, including the 5 mm base studs), exactly the number
#     you would type into the GridfinityGenerator plugin for Bin height Z.
#   - "ledgeDrop" is measured DOWN from the top face of the generated SOLID
#     bin (the top of the walls, where the stacking lip begins) to the ledge
#     surface that the battery slots are cut into.
#   - "slotDepth" is measured down from the ledge surface.
#   - "tipDepth" is the extra depth of the tip (button) recess below the
#     bottom of the slot. The battery rests on its shoulder at the slot
#     bottom; the button hangs in the recess and never carries weight.
#   - "batteryLength" is the full overall battery length (button included),
#     used only for the stackability fit-check readout.

BATTERY_TYPES = ['AAA', 'AA', 'CR123', '9V', '18650']

BATTERY_DEFAULTS = {
    'AAA': dict(
        isRound=True,
        slotDiaLen=11.0,   # slot diameter
        slotWidth=0.0,     # unused for round batteries
        slotDepth=30.0,
        tipDiaLen=4.0,     # tip recess diameter
        tipWidth=0.0,      # unused for round batteries
        tipDepth=2.5,
        ledgeDrop=15.0,
        batteryLength=44.5,
    ),
    'AA': dict(
        isRound=True,
        slotDiaLen=14.75,
        slotWidth=0.0,
        slotDepth=36.0,    # deepened from 26 so a 50.5 mm cell stays below the wall top
        tipDiaLen=6.0,
        tipWidth=0.0,
        tipDepth=2.5,
        ledgeDrop=15.0,
        batteryLength=50.5,
    ),
    'CR123': dict(
        isRound=True,
        slotDiaLen=17.0,
        slotWidth=0.0,
        slotDepth=20.0,    # nudged from 19 for 0.5 mm margin at max cell length
        tipDiaLen=7.0,
        tipWidth=0.0,
        tipDepth=2.5,
        ledgeDrop=15.0,
        batteryLength=34.5,
    ),
    '18650': dict(
        isRound=True,
        slotDiaLen=19.0,   # 18.6 mm max cell dia + 0.4 clearance (unprotected cells)
        slotWidth=0.0,
        slotDepth=51.0,
        tipDiaLen=10.0,    # clears button-top positive terminals
        tipWidth=0.0,
        tipDepth=2.5,
        ledgeDrop=15.0,
        batteryLength=65.2,  # unprotected max; protected/button-top cells run 67-70,
                             # bump this (and slot depth) in the dialog for those
    ),
    '9V': dict(
        isRound=False,
        slotDiaLen=27.4,   # slot length (long side of the rectangle)
        slotWidth=17.5,    # slot width (short side of the rectangle)
        slotDepth=34.0,    # nudged from 32 for 0.5 mm margin at max cell length
        tipDiaLen=21.0,    # tip recess length (covers both snap terminals)
        tipWidth=9.0,      # tip recess width - measured, not nominal
        tipDepth=4.0,
        ledgeDrop=15.0,
        batteryLength=48.5,
    ),
}

# Fixed layout rules (defaults, editable in the dialog), mm
DEFAULT_MIN_SLOT_SPACING = 3.0   # minimum distance between slot walls
DEFAULT_MIN_WALL_CLEARANCE = 5.0 # minimum distance between a slot and the inner bin wall
DEFAULT_LEDGE_FILLET_RADIUS = 3.0  # fillet where the ledge meets the wall above it
DEFAULT_HEADROOM = 0.5           # extra clearance wanted between battery top and wall top
# Solid floor left under the deepest cut. The cut must never reach the
# underside of the bin body: the feet cover only part of that face, so a
# recess dipping below it breaks straight through wherever it lands over the
# gap between two feet. 1.0 mm matches the compartment floor thickness the
# gridfinity library itself uses.
DEFAULT_MIN_FLOOR_THICKNESS = 1.0
# Print layer height. When the bin height is NOT constrained to gridfinity
# units, the computed height is rounded up to a whole number of these so the
# top face lands on a layer boundary instead of part way through one. Set to 0
# to use the exact computed height.
DEFAULT_LAYER_HEIGHT = 0.2
# Rectangular slots (9V) only: let the generator fill the strip left over by a
# uniform grid with a row turned 90 degrees. Off, every slot faces the same
# way - fewer batteries, but a tidier bin.
DEFAULT_ALLOW_MIXED_LAYOUT = True

# ------------------------------------------------------------------ label tab
# An optional shelf across one corner of the ledge, carrying a short chemistry
# code. The battery size is deliberately not on it: you are looking down into
# the bin to read it, so you can already see what is in there, and a shorter
# label means a smaller shelf.
#
# The size is what makes it free. Every slot keeps the wall clearance from both
# walls, so in corner coordinates a slot only occupies x >= c and y >= c, while
# a right triangle on the corner only occupies x + y <= leg. While the leg
# stays within twice the clearance the two cannot overlap - on any bin, for any
# battery, in any corner. No measuring and no special cases.
CHEMISTRY_OTHER = 'Other'
CHEMISTRY_LABELS = [
    ('Alkaline', 'ALK'),
    ('Lithium', 'LI'),
    ('NiMH', 'NMH'),
    ('Li-ion', 'ION'),
    ('Rechargeable', 'RCH'),
    ('Carbon zinc', 'ZNC'),
    (CHEMISTRY_OTHER, ''),
]
CHEMISTRY_NAMES = [name for (name, _code) in CHEMISTRY_LABELS]

DEFAULT_TAB_ENABLED = False
# Two sizes matter for a corner shelf.
#
# FREE: a triangle with legs within twice the slot-to-wall clearance - 10 mm at
# the default - provably cannot reach a slot on any bin. But it only holds
# about 2.9 mm text, which is small to read across a drawer.
#
# ONE SLOT: 24 mm is the largest shelf that never costs more than a single slot
# on any bin from 1x2 to 5x5, for any battery, in any corner - measured across
# the whole matrix, not derived, and asserted in the tests. Past it an AAA 2x5
# starts losing two. 1x1 bins are excluded: an 18650 or CR123 1x1 holds a single
# battery and nobody prints one.
#
# The default sits just inside that, because a label you can actually read
# across a drawer is worth one battery out of twenty-five. Dial the height down
# to 2.9 mm for a free shelf; the readout states the cost either way.
ONE_SLOT_TAB_LEG = 24.0
# 5.9 mm is the tallest lettering that keeps every code in the table inside
# that 24 mm leg. The binding one is NMH, the widest of them at 3.31 cap
# heights; LI would take 9.6 mm. Raise it in the dialog for a short code and
# the readout will say what the bigger shelf costs.
DEFAULT_TAB_TEXT_HEIGHT = 5.9     # cap height, mm
DEFAULT_TAB_MARGIN = 0.6          # flat border around the text, mm
DEFAULT_TAB_TEXT_DEPTH = 0.4      # raised height, two 0.2 mm layers
DEFAULT_TAB_THICKNESS = 1.6       # shelf thickness at the corner, mm
DEFAULT_TAB_TOP_CLEARANCE = 1.0   # tab top below the wall top, mm
DEFAULT_TAB_CORNER = 'Back left'
DEFAULT_TAB_FONT = 'Arial'
# Faces whose character widths match the table the shelf is sized from.
# Helvetica and Liberation Sans are metric-compatible with Arial by design.
KNOWN_METRIC_FONTS = ('Arial', 'Helvetica', 'Liberation Sans')
# Bold, and not for looks: raised lettering is printed as walls, and a regular
# weight at this size has stems around 0.34 mm - narrower than the 0.42 mm line
# a 0.4 mm nozzle lays down, so the slicer discards the letters entirely and the
# label silently disappears. Bold takes the stems to about 0.53 mm.
DEFAULT_TAB_BOLD = True
# Thinnest stroke a common 0.4 mm nozzle will reliably print, mm.
MIN_PRINTABLE_STROKE = 0.45
MAX_TAB_CHARS = 3

# Colour is deliberately not here yet. Assigning a second filament to the
# lettering needs it to reach the slicer as its own part, and a body per letter
# is exactly what Bambu loaded as four scattered objects rather than one bin.
# Until that export path is worked out the text is joined into the bin and a
# generated bin is a single solid - see JOIN_TEXT_TO_BIN in the command.


def chemistryCode(name, override=''):
    """Label text for a chemistry: the table's code, or your own for Other."""
    if name == CHEMISTRY_OTHER:
        return override.strip().upper()
    for (label, code) in CHEMISTRY_LABELS:
        if label == name:
            return code
    return ''

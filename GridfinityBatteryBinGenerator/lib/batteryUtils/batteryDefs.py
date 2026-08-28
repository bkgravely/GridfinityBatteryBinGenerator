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

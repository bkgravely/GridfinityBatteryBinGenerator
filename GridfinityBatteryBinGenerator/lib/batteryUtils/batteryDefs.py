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
        tipDiaLen=14.0,    # tip recess length (covers both snap terminals)
        tipWidth=8.0,      # tip recess width
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
DEFAULT_BASE_DIP_ALLOWANCE = 0.5 # how far a cut may extend below the bin body into the
                                 # solid base studs before auto-height adds another unit

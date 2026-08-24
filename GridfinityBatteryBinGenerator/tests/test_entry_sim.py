# Simulation test for the command entry module, run OUTSIDE Fusion 360.
# Stubs the adsk API just enough to import the add-in package and drive
# readParams / applyBatteryDefaults / formatResultText / updateComputed.
# Run: python3 tests/test_entry_sim.py
import os
import sys
import types
from types import SimpleNamespace
from unittest.mock import MagicMock

HERE = os.path.dirname(os.path.abspath(__file__))
PKG_PARENT = os.path.dirname(os.path.dirname(HERE) + '/x')  # /home/claude
PKG_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(PKG_PARENT))

# ---- stub adsk before importing the package
adsk = types.ModuleType('adsk')
adsk.core = MagicMock(name='adsk.core')
adsk.fusion = MagicMock(name='adsk.fusion')
sys.modules['adsk'] = adsk
sys.modules['adsk.core'] = adsk.core
sys.modules['adsk.fusion'] = adsk.fusion

pkgName = os.path.basename(PKG_PARENT)  # GridfinityBatteryBinGenerator
entry = __import__(pkgName + '.commands.commandCreateBatteryBin.entry',
                   fromlist=['entry'])
layoutMod = __import__(pkgName + '.lib.batteryUtils.layout', fromlist=['layout'])
defsMod = __import__(pkgName + '.lib.batteryUtils.batteryDefs', fromlist=['batteryDefs'])

# make .cast() a passthrough so our fakes flow through readParams
for clsName in ('ValueCommandInput', 'IntegerSpinnerCommandInput',
                'BoolValueCommandInput', 'TextBoxCommandInput',
                'DropDownCommandInput'):
    getattr(adsk.core, clsName).cast = lambda x: x

PASS = 0
FAIL = 0


def check(name, cond, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print('FAIL: {} {}'.format(name, detail))


class FakeInputs:
    def __init__(self, items):
        self.items = items

    def itemById(self, inputId):
        return self.items[inputId]


def mmInput(mm):
    return SimpleNamespace(value=mm / 10.0, isVisible=True, isEnabled=True)


def makeInputs(battery='AA', binX=2, binY=3, autoHeight=True, units=8):
    e = entry
    d = defsMod.BATTERY_DEFAULTS[battery]
    items = {
        e.BATTERY_TYPE_ID: SimpleNamespace(selectedItem=SimpleNamespace(name=battery)),
        e.BIN_WIDTH_ID: SimpleNamespace(value=binX),
        e.BIN_LENGTH_ID: SimpleNamespace(value=binY),
        e.AUTO_HEIGHT_ID: SimpleNamespace(value=autoHeight),
        e.BIN_HEIGHT_ID: SimpleNamespace(value=units, isEnabled=True),
        e.SLOT_DIA_LEN_ID: mmInput(d['slotDiaLen']),
        e.SLOT_WIDTH_ID: mmInput(d['slotWidth']),
        e.SLOT_DEPTH_ID: mmInput(d['slotDepth']),
        e.TIP_DIA_LEN_ID: mmInput(d['tipDiaLen']),
        e.TIP_WIDTH_ID: mmInput(d['tipWidth']),
        e.TIP_DEPTH_ID: mmInput(d['tipDepth']),
        e.LEDGE_DROP_ID: mmInput(d['ledgeDrop']),
        e.BATTERY_LENGTH_ID: mmInput(d['batteryLength']),
        e.MIN_SPACING_ID: mmInput(3.0),
        e.WALL_CLEARANCE_ID: mmInput(5.0),
        e.LEDGE_FILLET_ID: mmInput(3.0),
        e.HEADROOM_ID: mmInput(0.5),
        e.BASE_DIP_ID: mmInput(0.5),
        e.WITH_LIP_ID: SimpleNamespace(value=True),
        e.LIP_NOTCHES_ID: SimpleNamespace(value=False),
        e.WALL_THICKNESS_ID: mmInput(2.15),
        e.SCREW_HOLES_ID: SimpleNamespace(value=False),
        e.SCREW_DIAMETER_ID: mmInput(3.0),
        e.MAGNET_CUTOUTS_ID: SimpleNamespace(value=False),
        e.MAGNET_DIAMETER_ID: mmInput(6.5),
        e.MAGNET_DEPTH_ID: mmInput(2.4),
        e.BASE_WIDTH_UNIT_ID: mmInput(42.0),
        e.BASE_LENGTH_UNIT_ID: mmInput(42.0),
        e.HEIGHT_UNIT_ID: mmInput(7.0),
        e.XY_CLEARANCE_ID: mmInput(0.25),
        e.SHOW_PREVIEW_ID: SimpleNamespace(value=False),
        e.RESULT_TEXT_ID: SimpleNamespace(formattedText=''),
    }
    return FakeInputs(items)


expectedAuto = {'AAA': 8, 'AA': 9, 'CR123': 6, '9V': 9}
expectedCount2x3 = {'AAA': 41, 'AA': 25, 'CR123': 20, '9V': 10}

for bat in defsMod.BATTERY_TYPES:
    inputs = makeInputs(battery=bat)
    p = entry.readParams(inputs)
    check(bat + ' no errors', p['errors'] == [], p['errors'])
    check(bat + ' no warnings', p['warnings'] == [], p['warnings'])
    check(bat + ' auto units', p['units'] == expectedAuto[bat], p['units'])
    check(bat + ' count 2x3', p['layout']['count'] == expectedCount2x3[bat],
          p['layout']['count'] if p['layout'] else None)
    txt = entry.formatResultText(p)
    check(bat + ' result text mentions count',
          str(expectedCount2x3[bat]) in txt, txt)
    check(bat + ' result says stackable', 'Stackable' in txt, txt)
    print('{:6s} u={} count={} :: {}'.format(bat, p['units'],
                                             p['layout']['count'], p['layout']['desc']))

# manual height too short -> warning about base studs
inputs = makeInputs(battery='AA', autoHeight=False, units=8)
p = entry.readParams(inputs)
check('AA manual 8u warns about base', any('base studs' in w for w in p['warnings']),
      p['warnings'])

# battery too long for containment -> stackability warning
inputs = makeInputs(battery='AA')
inputs.items[entry.SLOT_DEPTH_ID].value = 2.0  # 20 mm slot depth
p = entry.readParams(inputs)
check('shallow AA slot warns not stackable',
      any('ABOVE the wall top' in w for w in p['warnings']), p['warnings'])

# tip recess larger than slot -> error
inputs = makeInputs(battery='AAA')
inputs.items[entry.TIP_DIA_LEN_ID].value = 1.2  # 12 mm > 11 mm slot
p = entry.readParams(inputs)
check('oversize tip recess is an error', len(p['errors']) == 1, p['errors'])

# 9V in 1x1 -> no fit error
inputs = makeInputs(battery='9V', binX=1, binY=1)
p = entry.readParams(inputs)
check('9V 1x1 no-fit error', any('No slot fits' in x for x in p['errors']), p['errors'])

# applyBatteryDefaults writes the right values and toggles 9V-only visibility
inputs = makeInputs(battery='9V')
entry.applyBatteryDefaults(inputs)
check('9V slot width applied',
      abs(inputs.itemById(entry.SLOT_WIDTH_ID).value * 10 - 17.5) < 1e-9,
      inputs.itemById(entry.SLOT_WIDTH_ID).value)
check('9V width visible', inputs.itemById(entry.SLOT_WIDTH_ID).isVisible is True)
inputs.items[entry.BATTERY_TYPE_ID].selectedItem.name = 'AAA'
entry.applyBatteryDefaults(inputs)
check('AAA width hidden', inputs.itemById(entry.SLOT_WIDTH_ID).isVisible is False)
check('AAA slot dia applied',
      abs(inputs.itemById(entry.SLOT_DIA_LEN_ID).value * 10 - 11.0) < 1e-9)

# updateComputed drives the height spinner + result text
inputs = makeInputs(battery='AA')
inputs.items[entry.BIN_HEIGHT_ID].value = 3
p = entry.updateComputed(inputs)
check('updateComputed returns params', p is not None)
check('height spinner set to auto', inputs.itemById(entry.BIN_HEIGHT_ID).value == 9,
      inputs.itemById(entry.BIN_HEIGHT_ID).value)
check('spinner disabled on auto', inputs.itemById(entry.BIN_HEIGHT_ID).isEnabled is False)
check('result text filled', len(inputs.itemById(entry.RESULT_TEXT_ID).formattedText) > 20)

# ---- regression: inputChanged must work through firingEvent.sender even when
# args.inputs is the crippled group-limited collection Fusion hands out
adsk.core.Command.cast = lambda x: x

class CrippledInputs:
    """Simulates the inputChanged args.inputs quirk: finds nothing."""
    def itemById(self, inputId):
        return None

def fireInputChanged(inputs, changedId):
    cmd = SimpleNamespace(commandInputs=inputs)
    args = SimpleNamespace(
        input=SimpleNamespace(id=changedId),
        inputs=CrippledInputs(),
        firingEvent=SimpleNamespace(sender=cmd))
    entry.command_input_changed(args)

def fireValidate(inputs):
    cmd = SimpleNamespace(commandInputs=inputs)
    args = SimpleNamespace(inputs=CrippledInputs(),
                           firingEvent=SimpleNamespace(sender=cmd),
                           areInputsValid=None)
    entry.command_validate_input(args)
    return args.areInputsValid

inputs = makeInputs(battery='AA')
inputs.items[entry.BATTERY_TYPE_ID].selectedItem.name = 'CR123'
fireInputChanged(inputs, entry.BATTERY_TYPE_ID)
check('dropdown change applies CR123 slot dia',
      abs(inputs.itemById(entry.SLOT_DIA_LEN_ID).value * 10 - 17.0) < 1e-9,
      inputs.itemById(entry.SLOT_DIA_LEN_ID).value * 10)
p = entry.readParams(inputs)
check('CR123 after switch: 20 slots', p['layout']['count'] == 20, p['layout'])
check('CR123 after switch: 6 u', p['units'] == 6, p['units'])
check('CR123 after switch validates', fireValidate(inputs) is True)

inputs.items[entry.BATTERY_TYPE_ID].selectedItem.name = '9V'
fireInputChanged(inputs, entry.BATTERY_TYPE_ID)
check('9V after switch: slot width 17.5',
      abs(inputs.itemById(entry.SLOT_WIDTH_ID).value * 10 - 17.5) < 1e-9)
check('9V after switch validates (OK not greyed)', fireValidate(inputs) is True)
p = entry.readParams(inputs)
check('9V after switch: 10 slots', p['layout']['count'] == 10, p['layout'])

print('regression: {} passed, {} failed'.format(PASS, FAIL))
sys.exit(1 if FAIL else 0)

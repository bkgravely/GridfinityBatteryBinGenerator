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
                'StringValueCommandInput', 'DropDownCommandInput'):
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


def makeInputs(battery='AA', binX=2, binY=3, autoHeight=True, units=8,
               constrainUnits=True, heightMm=56.0, layerHeight=None,
               allowMixed=None, tab=False, chemistry='Alkaline', chemOther='',
               tabCorner='Back left', tabTextHeight=None, tabFont='Arial'):
    if layerHeight is None:
        layerHeight = defsMod.DEFAULT_LAYER_HEIGHT
    if allowMixed is None:
        allowMixed = defsMod.DEFAULT_ALLOW_MIXED_LAYOUT
    if tabTextHeight is None:
        tabTextHeight = defsMod.DEFAULT_TAB_TEXT_HEIGHT
    e = entry
    d = defsMod.BATTERY_DEFAULTS[battery]
    items = {
        e.BATTERY_TYPE_ID: SimpleNamespace(selectedItem=SimpleNamespace(name=battery)),
        e.BIN_WIDTH_ID: SimpleNamespace(value=binX),
        e.BIN_LENGTH_ID: SimpleNamespace(value=binY),
        e.AUTO_HEIGHT_ID: SimpleNamespace(value=autoHeight),
        e.BIN_HEIGHT_ID: SimpleNamespace(value=units, isEnabled=True, isVisible=True),
        e.BIN_HEIGHT_MM_ID: SimpleNamespace(value=heightMm/10.0, isEnabled=True, isVisible=True),
        e.CONSTRAIN_UNITS_ID: SimpleNamespace(value=constrainUnits),
        e.LAYER_HEIGHT_ID: mmInput(layerHeight),
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
        e.MIN_FLOOR_ID: mmInput(1.0),
        e.MIXED_LAYOUT_ID: SimpleNamespace(value=allowMixed),
        e.TAB_ENABLED_ID: SimpleNamespace(value=tab),
        e.CHEMISTRY_ID: SimpleNamespace(selectedItem=SimpleNamespace(name=chemistry)),
        e.CHEMISTRY_OTHER_ID: SimpleNamespace(value=chemOther, isEnabled=True, isVisible=True),
        e.TAB_CORNER_ID: SimpleNamespace(selectedItem=SimpleNamespace(name=tabCorner)),
        e.TAB_TEXT_HEIGHT_ID: mmInput(tabTextHeight),
        e.TAB_FONT_ID: SimpleNamespace(value=tabFont),
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


expectedAuto = {'AAA': 8, 'AA': 9, 'CR123': 7, '9V': 9, '18650': 11}
expectedCount2x3 = {'AAA': 41, 'AA': 25, 'CR123': 20, '9V': 11, '18650': 15}

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
check('AA manual 8u warns about breaking through',
      any('break through' in w or 'floor left' in w for w in p['warnings']), p['warnings'])

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
check('CR123 after switch: 7 u', p['units'] == 7, p['units'])
check('CR123 after switch validates', fireValidate(inputs) is True)

inputs.items[entry.BATTERY_TYPE_ID].selectedItem.name = '9V'
fireInputChanged(inputs, entry.BATTERY_TYPE_ID)
check('9V after switch: slot width 17.5',
      abs(inputs.itemById(entry.SLOT_WIDTH_ID).value * 10 - 17.5) < 1e-9)
check('9V after switch validates (OK not greyed)', fireValidate(inputs) is True)
p = entry.readParams(inputs)
check('9V after switch: 11 slots', p['layout']['count'] == 11, p['layout'])


# ---- chemistry label tab
check('label tab is off by default', defsMod.DEFAULT_TAB_ENABLED is False)
# One body per bin. Separate letter bodies are what a second filament would
# need, but Fusion writes a body per 3MF object and Bambu loads those as loose
# objects dropped to the plate, so the letters arrive scattered beside the bin.
check('the lettering is joined into the bin', entry.JOIN_TEXT_TO_BIN is True)
off = entry.readParams(makeInputs(battery='AA', binX=2, binY=3))
check('no tab means no tab geometry', off['tabTri'] is None, off['tabTri'])
check('no tab costs nothing', off['tabBlocked'] == 0)
check('no tab, no readout line', 'Label' not in entry.formatResultText(off))

for chem, code in defsMod.CHEMISTRY_LABELS:
    if chem == defsMod.CHEMISTRY_OTHER:
        continue
    p = entry.readParams(makeInputs(battery='AA', binX=2, binY=3, tab=True, chemistry=chem))
    check(chem + ' abbreviates to ' + code, p['tabText'] == code, p['tabText'])
    check(chem + ' tab is valid', p['errors'] == [], p['errors'])
    check(chem + ' tab fits in three characters', len(p['tabText']) <= defsMod.MAX_TAB_CHARS)

# the cost, which is the whole reason the corner was chosen
p = entry.readParams(makeInputs(battery='AA', binX=2, binY=3, tab=True))
check('AA 2x3 shelf costs at most one slot', p['tabBlocked'] <= 1, p['tabBlocked'])
check('tab count reflects the loss', p['layout']['count'] == off['layout']['count'] - p['tabBlocked'])
check('a default shelf does not warn', p['warnings'] == [], p['warnings'])
check('readout names the label', '"ALK"' in entry.formatResultText(p), entry.formatResultText(p))
check('readout calls it a corner shelf', 'corner shelf' in entry.formatResultText(p))
check('readout states the stroke width', 'mm strokes' in entry.formatResultText(p),
      entry.formatResultText(p))
check('default lettering is printable',
      p['tabStem'] >= defsMod.MIN_PRINTABLE_STROKE, p['tabStem'])
check('lettering is bold by default', p['tabBold'] is True)

# text too small to print is the failure that silently produced a blank shelf
tiny = entry.readParams(makeInputs(battery='AA', tab=True, tabTextHeight=1.5))
check('unprintably thin lettering warns',
      any('stems' in w for w in tiny['warnings']), tiny['warnings'])
check('the warning names a workable height',
      any('or more' in w for w in tiny['warnings']), tiny['warnings'])
check('readout states the cost',
      'costs no slots' in entry.formatResultText(p) or 'costs 1 slot' in entry.formatResultText(p),
      entry.formatResultText(p))

# a tab must never move the slots that survive
for bat in defsMod.BATTERY_TYPES:
    a = entry.readParams(makeInputs(battery=bat, binX=3, binY=3))
    b = entry.readParams(makeInputs(battery=bat, binX=3, binY=3, tab=True))
    check(bat + ' shelf costs at most one slot', b['tabBlocked'] <= 1, b['tabBlocked'])
    check(bat + ' surviving slots do not move',
          b['layout']['centers'] == [c for c in a['layout']['centers']
                                     if c in b['layout']['centers']])
    check(bat + ' shelf stays inside the one-slot size',
          b['tabLeg'] <= defsMod.ONE_SLOT_TAB_LEG + 1e-9, b['tabLeg'])

# every corner works, sits on the floor corner, and costs nothing
for corner in layoutMod.TAB_CORNERS:
    p = entry.readParams(makeInputs(battery='AA', binX=2, binY=3, tab=True, tabCorner=corner))
    (cx, cy) = p['tabTri'][0]
    check(corner + ' shelf sits on that corner',
          (abs(cx) < 1e-9 or abs(cx - p['floorW']) < 1e-9)
          and (abs(cy) < 1e-9 or abs(cy - p['floorL']) < 1e-9), p['tabTri'])
    check(corner + ' shelf is inside the floor',
          all(-1e-9 <= x <= p['floorW'] + 1e-9 and -1e-9 <= y <= p['floorL'] + 1e-9
              for (x, y) in p['tabTri']), p['tabTri'])
    check(corner + ' shelf costs at most one slot', p['tabBlocked'] <= 1, p['tabBlocked'])

# Other: free text, capped by what the corner physically holds
p = entry.readParams(makeInputs(battery='AA', tab=True, chemistry='Other', chemOther=''))
check('Other with no text is rejected', any('Enter the label' in e for e in p['errors']), p['errors'])
p = entry.readParams(makeInputs(battery='AA', tab=True, chemistry='Other', chemOther='NiMH'))
check('four characters are rejected', any('characters' in e for e in p['errors']), p['errors'])
p = entry.readParams(makeInputs(battery='AA', tab=True, chemistry='Other', chemOther=' li '))
check('free text is trimmed and upper-cased', p['tabText'] == 'LI', p['tabText'])
check('trimmed free text is valid', p['errors'] == [], p['errors'])

# a shorter label earns a smaller tab
wide = entry.readParams(makeInputs(battery='AA', tab=True, chemistry='Alkaline'))
narrow = entry.readParams(makeInputs(battery='AA', tab=True, chemistry='Lithium'))
check('two letters make a smaller shelf', narrow['tabLeg'] < wide['tabLeg'],
      (narrow['tabLeg'], wide['tabLeg']))
check('the default shelf is inside the one-slot size',
      wide['tabLeg'] <= defsMod.ONE_SLOT_TAB_LEG + 1e-9, wide['tabLeg'])

# oversized text is allowed, but it has to say what it costs
big = entry.readParams(makeInputs(battery='AA', binX=2, binY=3, tab=True, tabTextHeight=9.0))
check('a shelf past the one-slot size is flagged',
      big['tabLeg'] > defsMod.ONE_SLOT_TAB_LEG, big['tabLeg'])
check('oversized shelf warns',
      any('never costs more than one' in w for w in big['warnings']), big['warnings'])
check('oversized shelf names a workable text height',
      any('holds it to one slot' in w for w in big['warnings']), big['warnings'])


# ---- mixed slot orientations: on by default, and optional
check('mixed layout defaults on', defsMod.DEFAULT_ALLOW_MIXED_LAYOUT is True)
for (bx, by, mixedCount, uniformCount) in ((2, 3, 11, 10), (3, 3, 18, 15), (3, 4, 26, 25)):
    on = entry.readParams(makeInputs(battery='9V', binX=bx, binY=by, allowMixed=True))
    off = entry.readParams(makeInputs(battery='9V', binX=bx, binY=by, allowMixed=False))
    check('9V {}x{} mixed count'.format(bx, by), on['layout']['count'] == mixedCount,
          (on['layout']['count'], on['layout']['desc']))
    check('9V {}x{} uniform count'.format(bx, by), off['layout']['count'] == uniformCount,
          (off['layout']['count'], off['layout']['desc']))
    # every slot the same way round when it is off
    check('9V {}x{} uniform has one footprint'.format(bx, by),
          len(set(off['layout']['slotSizes'])) == 1, set(off['layout']['slotSizes']))
    check('9V {}x{} mixed uses both footprints'.format(bx, by),
          len(set(on['layout']['slotSizes'])) == 2, set(on['layout']['slotSizes']))
    # and the readout says what turning it off costs
    check('9V {}x{} readout names the gain'.format(bx, by),
          '{} more'.format(mixedCount - uniformCount) in entry.formatResultText(off),
          entry.formatResultText(off))
    check('9V {}x{} readout silent when mixed is on'.format(bx, by),
          'more would fit' not in entry.formatResultText(on))

# round batteries are unaffected either way
for bat in ('AAA', 'AA', 'CR123', '18650'):
    on = entry.readParams(makeInputs(battery=bat, allowMixed=True))
    off = entry.readParams(makeInputs(battery=bat, allowMixed=False))
    check(bat + ' ignores the mixed setting',
          on['layout']['count'] == off['layout']['count'], (on['layout'], off['layout']))
    check(bat + ' readout silent about mixed orientations',
          'more would fit' not in entry.formatResultText(off))


# ---- height: gridfinity units are optional, only the footprint is fixed
# exact minimum heights, with the layer rounding switched off
expectedRawMm = {'AAA': 53.5, 'AA': 59.5, 'CR123': 43.5, '9V': 59.0, '18650': 74.5}
for bat, expected in expectedRawMm.items():
    p = entry.readParams(makeInputs(battery=bat, constrainUnits=False, layerHeight=0.0))
    check(bat + ' exact free height', abs(p['totalHeightMm'] - expected) < 1e-6,
          (p['totalHeightMm'], expected))

# ...and the same heights rounded up to a whole 0.2 mm layer, which is what
# the dialog offers by default
expectedFreeMm = {'AAA': 53.6, 'AA': 59.6, 'CR123': 43.6, '9V': 59.0, '18650': 74.6}
for bat, expected in expectedFreeMm.items():
    p = entry.readParams(makeInputs(battery=bat, constrainUnits=False))
    check(bat + ' free height', abs(p['totalHeightMm'] - expected) < 1e-6,
          (p['totalHeightMm'], expected))
    # a free-height bin must still keep its floor and stay stackable
    check(bat + ' free height keeps floor',
          p['fit']['floorThickness'] >= 1.0 - 1e-6, p['fit']['floorThickness'])
    check(bat + ' free height stackable', p['fit']['margin'] >= -1e-6, p['fit']['margin'])
    check(bat + ' free height no errors', p['errors'] == [], p['errors'])
    # and never be taller than the unit-rounded one
    q = entry.readParams(makeInputs(battery=bat, constrainUnits=True))
    check(bat + ' free height is not taller',
          p['totalHeightMm'] <= q['totalHeightMm'] + 1e-9,
          (p['totalHeightMm'], q['totalHeightMm']))

# CR123 is the case that motivated this: a whole unit of dead plastic
free = entry.readParams(makeInputs(battery='CR123', constrainUnits=False))
unit = entry.readParams(makeInputs(battery='CR123', constrainUnits=True))
check('CR123 saves 5.4mm unconstrained',
      abs((unit['totalHeightMm'] - free['totalHeightMm']) - 5.4) < 1e-6,
      (unit['totalHeightMm'], free['totalHeightMm']))
check('constrained result mentions the shorter option',
      'shorter' in entry.formatResultText(unit), entry.formatResultText(unit))

# ---- layer rounding: a free height must land on a whole layer boundary
for bat in defsMod.BATTERY_TYPES:
    for layer in (0.2, 0.15, 0.28):
        p = entry.readParams(makeInputs(battery=bat, constrainUnits=False, layerHeight=layer))
        q = entry.readParams(makeInputs(battery=bat, constrainUnits=False, layerHeight=0.0))
        check('{} height is a whole {}mm layer'.format(bat, layer),
              layoutMod.isMultipleOf(p['totalHeightMm'], layer), p['totalHeightMm'])
        # rounding is always UP, and never by more than one layer
        check('{} layer rounding adds under one {}mm layer'.format(bat, layer),
              -1e-9 <= p['totalHeightMm'] - q['totalHeightMm'] < layer - 1e-9,
              (p['totalHeightMm'], q['totalHeightMm']))
        # taller cannot cost floor or stackability
        check('{} layered height keeps floor'.format(bat),
              p['fit']['floorThickness'] >= 1.0 - 1e-6, p['fit']['floorThickness'])
        check('{} layered height stackable'.format(bat), p['fit']['margin'] >= -1e-6)

# the rounding only applies off the unit grid, and only when auto height drives it
p = entry.readParams(makeInputs(battery='AA', constrainUnits=True))
check('constrained height ignores the layer step',
      abs(p['totalHeightMm'] - 63.0) < 1e-6, p['totalHeightMm'])
check('layer note shown only off the unit grid',
      'layer' not in entry.formatResultText(p), entry.formatResultText(p))
check('layer note shown for a free height',
      'layer' in entry.formatResultText(entry.readParams(
          makeInputs(battery='AA', constrainUnits=False))))

# a manual height part way through a layer is honoured, but flagged
p = entry.readParams(makeInputs(battery='AA', autoHeight=False, constrainUnits=False,
                                heightMm=59.55))
check('manual off-layer height honoured', abs(p['totalHeightMm'] - 59.55) < 1e-6,
      p['totalHeightMm'])
check('manual off-layer height warns',
      any('layers' in w for w in p['warnings']), p['warnings'])
p = entry.readParams(makeInputs(battery='AA', autoHeight=False, constrainUnits=False,
                                heightMm=59.6))
check('manual on-layer height does not warn',
      not any('layers' in w for w in p['warnings']), p['warnings'])

# constrained mode still yields whole units
for bat in defsMod.BATTERY_TYPES:
    p = entry.readParams(makeInputs(battery=bat, constrainUnits=True))
    check(bat + ' constrained height is whole units',
          abs(p['units'] - round(p['units'])) < 1e-9, p['units'])

# a manual free height is honoured, and a silly one is rejected
p = entry.readParams(makeInputs(battery='AA', autoHeight=False,
                                constrainUnits=False, heightMm=70.0))
check('manual free height honoured', abs(p['totalHeightMm'] - 70.0) < 1e-6, p['totalHeightMm'])
p = entry.readParams(makeInputs(battery='AA', autoHeight=False,
                                constrainUnits=False, heightMm=4.0))
check('height below the base errors', any('at least' in e for e in p['errors']), p['errors'])

# ---- the name users actually see in Solid > Create
check('command is named for the menu', entry.CMD_NAME == 'Gridfinity Battery Bin', entry.CMD_NAME)
check('description mentions every battery type',
      all(b in entry.CMD_Description for b in ('AAA', 'AA', 'CR123', '9V', '18650')),
      entry.CMD_Description)
check('dialog blurb matches the command name',
      'Gridfinity Battery Bin' in entry.INFO_TEXT, entry.INFO_TEXT[:80])

# ---- logo is fixed, not a dialog option: same on every bin, always on
logoMod = __import__(pkgName + '.lib.batteryUtils.logoUtils', fromlist=['logoUtils'])

for bat in defsMod.BATTERY_TYPES:
    p = entry.readParams(makeInputs(battery=bat))
    check(bat + ' logo path is the bundled one', p['logoPath'] == entry.BUNDLED_LOGO_PATH)
    check(bat + ' logo on corner foot', p['logoPlacement'] == 'Corner foot', p['logoPlacement'])
    check(bat + ' logo size fixed', abs(p['logoSize'] - logoMod.LOGO_SIZE) < 1e-9)
    check(bat + ' logo depth fixed', abs(p['logoDepth'] - logoMod.LOGO_DEPTH) < 1e-9)
    check(bat + ' logo not re-mirrored', p['logoMirror'] is False)
    check(bat + ' logo not rotated', p['logoRotation'] == 0)
    check(bat + ' logo adds no errors', p['errors'] == [], p['errors'])
    check(bat + ' logo adds no warnings', p['warnings'] == [], p['warnings'])
    check(bat + ' result reports the logo', 'Logo engraved' in entry.formatResultText(p))

# no logo controls may leak back into the dialog
for leaked in ('LOGO_ENABLED_ID', 'LOGO_PATH_ID', 'LOGO_BROWSE_ID', 'LOGO_SIZE_ID',
               'LOGO_PLACEMENT_ID', 'LOGO_MIRROR_ID', 'LOGO_ROTATION_ID', 'LOGO_DEPTH_ID'):
    check('no ' + leaked + ' input', not hasattr(entry, leaked))

# the bundled artwork must actually be there and be importable vector art
check('bundled logo exists', os.path.isfile(entry.BUNDLED_LOGO_PATH))
with open(entry.BUNDLED_LOGO_PATH, 'r', encoding='utf-8') as handle:
    logoText = handle.read()
check('bundled logo is svg', '<svg' in logoText)
check('bundled logo has paths', logoText.count('<path') >= 1, logoText.count('<path'))
check('bundled logo has no live text', '<text' not in logoText)
check('bundled logo fits a foot',
      logoMod.LOGO_SIZE <= logoMod.maxLogoWidth(42.0, 0.25) + 1e-9,
      (logoMod.LOGO_SIZE, logoMod.maxLogoWidth(42.0, 0.25)))

# a missing bundled file is the one logo condition that blocks generation
inputs = makeInputs(battery='AA')
realPath = entry.BUNDLED_LOGO_PATH
try:
    entry.BUNDLED_LOGO_PATH = 'C:/nope/missing.svg'
    p = entry.readParams(inputs)
    check('missing bundled logo errors', any('reinstall' in e for e in p['errors']), p['errors'])
finally:
    entry.BUNDLED_LOGO_PATH = realPath

print('regression: {} passed, {} failed'.format(PASS, FAIL))
sys.exit(1 if FAIL else 0)

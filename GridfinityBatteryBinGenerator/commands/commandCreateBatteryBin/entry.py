import adsk.core, adsk.fusion, traceback
import os
import math
import tempfile

from ...lib import configUtils
from ...lib import fusion360utils as futil
from ... import config
from ...lib.gridfinityUtils import combineUtils
from ...lib.gridfinityUtils import geometryUtils
from ...lib.gridfinityUtils import commonUtils
from ...lib.gridfinityUtils import const
from ...lib.gridfinityUtils.baseGenerator import createBaseBodyPattern, cutBaseClearance
from ...lib.gridfinityUtils.baseGeneratorInput import BaseGeneratorInput
from ...lib.gridfinityUtils.binBodyGenerator import createGridfinityBinBody
from ...lib.gridfinityUtils.binBodyGeneratorInput import BinBodyGeneratorInput
from ...lib.gridfinityUtils.binBodyCutoutGenerator import createGridfinityBinBodyCutout
from ...lib.gridfinityUtils.binBodyCutoutGeneratorInput import BinBodyCutoutGeneratorInput
from ...lib.ui.unsupportedDesignTypeException import UnsupportedDesignTypeException
from ...lib.batteryUtils import layout
from ...lib.batteryUtils import batteryDefs
from ...lib.batteryUtils import logoUtils

app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdBatteryBin'
CMD_NAME = 'Gridfinity Battery Bin'
CMD_Description = ('Create a Gridfinity bin with a maximized grid of tip-down '
                   'battery slots (AAA, AA, CR123, 9V, 18650)')

IS_PROMOTED = True

WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidCreatePanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')
CONFIG_FOLDER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'commandConfig')

local_handlers = []

# ---------------------------------------------------------------- input ids
INFO_GROUP_ID = 'bb_info_group'
BATTERY_GROUP_ID = 'bb_battery_group'
SIZE_GROUP_ID = 'bb_size_group'
SLOT_GROUP_ID = 'bb_slot_group'
RULES_GROUP_ID = 'bb_rules_group'
FEATURES_GROUP_ID = 'bb_features_group'
ADVANCED_GROUP_ID = 'bb_advanced_group'
PREVIEW_GROUP_ID = 'bb_preview_group'

INFO_TEXT_ID = 'bb_info_text'
BATTERY_TYPE_ID = 'bb_battery_type'
BIN_WIDTH_ID = 'bb_bin_width_u'
BIN_LENGTH_ID = 'bb_bin_length_u'
AUTO_HEIGHT_ID = 'bb_auto_height'
BIN_HEIGHT_ID = 'bb_bin_height_u'

SLOT_DIA_LEN_ID = 'bb_slot_dia_len'
SLOT_WIDTH_ID = 'bb_slot_width'
SLOT_DEPTH_ID = 'bb_slot_depth'
TIP_DIA_LEN_ID = 'bb_tip_dia_len'
TIP_WIDTH_ID = 'bb_tip_width'
TIP_DEPTH_ID = 'bb_tip_depth'
LEDGE_DROP_ID = 'bb_ledge_drop'
BATTERY_LENGTH_ID = 'bb_battery_length'

MIN_SPACING_ID = 'bb_min_spacing'
WALL_CLEARANCE_ID = 'bb_wall_clearance'
LEDGE_FILLET_ID = 'bb_ledge_fillet'
HEADROOM_ID = 'bb_headroom'
BASE_DIP_ID = 'bb_base_dip'

WITH_LIP_ID = 'bb_with_lip'
LIP_NOTCHES_ID = 'bb_lip_notches'
WALL_THICKNESS_ID = 'bb_wall_thickness'
SCREW_HOLES_ID = 'bb_screw_holes'
SCREW_DIAMETER_ID = 'bb_screw_diameter'
MAGNET_CUTOUTS_ID = 'bb_magnet_cutouts'
MAGNET_DIAMETER_ID = 'bb_magnet_diameter'
MAGNET_DEPTH_ID = 'bb_magnet_depth'

BASE_WIDTH_UNIT_ID = 'bb_base_width_unit'
BASE_LENGTH_UNIT_ID = 'bb_base_length_unit'
HEIGHT_UNIT_ID = 'bb_height_unit'
XY_CLEARANCE_ID = 'bb_xy_clearance'

SHOW_PREVIEW_ID = 'bb_show_preview'
RESULT_TEXT_ID = 'bb_result_text'

BUNDLED_LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'resources', 'logo.svg')

INFO_TEXT = ('<b>Gridfinity Battery Bin</b> — builds a Gridfinity bin '
             '(geometry from the GridfinityGenerator add-in library) and cuts a '
             'maximized grid of tip-down battery slots with a tip recess so the '
             'battery rests on its shoulder, never on the button. '
             'Slot layout keeps the minimum slot-to-slot and slot-to-wall '
             'distances and is centered in the bin.')

# guard so programmatic input updates don't recurse through input_changed
_updatingInputs = False


def getErrorMessage(text='An unknown error occurred, please validate your inputs and try again'):
    stackTrace = traceback.format_exc()
    return f'{text}:<br>{stackTrace}'


def showErrorInMessageBox(text='An unknown error occurred, please validate your inputs and try again'):
    if ui:
        ui.messageBox(getErrorMessage(text), f'{CMD_NAME} Error')


# ------------------------------------------------------------------ start/stop
def start():
    try:
        futil.log(f'{CMD_NAME} Command Start Event')
        addinConfig = configUtils.readConfig(CONFIG_FOLDER_PATH)

        cmd_def = ui.commandDefinitions.itemById(CMD_ID)
        if not cmd_def:
            cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)
            futil.add_handler(cmd_def.commandCreated, command_created)
            workspace = ui.workspaces.itemById(WORKSPACE_ID)
            panel = workspace.toolbarPanels.itemById(PANEL_ID)
            control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)
            control.isPromoted = addinConfig['UI'].getboolean('is_promoted')
        ui.statusMessage = ''
    except Exception:
        futil.log(f'{CMD_NAME} Error occurred at the start, {getErrorMessage()}')
        showErrorInMessageBox(f'{CMD_NAME} critical error occurred at the start, the command will be unavailable')


def stop():
    futil.log(f'{CMD_NAME} Command Stop Event')
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control: adsk.core.CommandControl = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    addinConfig = configUtils.readConfig(CONFIG_FOLDER_PATH)
    if command_control:
        addinConfig['UI']['is_promoted'] = 'yes' if command_control.isPromoted else 'no'
    configUtils.writeConfig(addinConfig, CONFIG_FOLDER_PATH)

    if command_control:
        command_control.deleteMe()
    if command_definition:
        command_definition.deleteMe()


# ------------------------------------------------------------------ UI helpers
def mmValue(mm):
    return adsk.core.ValueInput.createByReal(mm / 10.0)


def addMmInput(parent: adsk.core.CommandInputs, inputId, name, mm):
    return parent.addValueInput(inputId, name, 'mm', mmValue(mm))


def applyBatteryDefaults(inputs: adsk.core.CommandInputs):
    """Load per-battery defaults into the editable dimension inputs."""
    dd: adsk.core.DropDownCommandInput = inputs.itemById(BATTERY_TYPE_ID)
    d = batteryDefs.BATTERY_DEFAULTS[dd.selectedItem.name]
    isRound = d['isRound']

    def setMm(inputId, mm):
        valueInput: adsk.core.ValueCommandInput = inputs.itemById(inputId)
        valueInput.value = mm / 10.0

    setMm(SLOT_DIA_LEN_ID, d['slotDiaLen'])
    setMm(SLOT_WIDTH_ID, d['slotWidth'] if not isRound else 0.0)
    setMm(SLOT_DEPTH_ID, d['slotDepth'])
    setMm(TIP_DIA_LEN_ID, d['tipDiaLen'])
    setMm(TIP_WIDTH_ID, d['tipWidth'] if not isRound else 0.0)
    setMm(TIP_DEPTH_ID, d['tipDepth'])
    setMm(LEDGE_DROP_ID, d['ledgeDrop'])
    setMm(BATTERY_LENGTH_ID, d['batteryLength'])

    inputs.itemById(SLOT_WIDTH_ID).isVisible = not isRound
    inputs.itemById(TIP_WIDTH_ID).isVisible = not isRound



# ------------------------------------------------------------------ parameters
def readParams(inputs: adsk.core.CommandInputs):
    """Read every dialog input, run the layout + height math, and collect
    warnings/errors. All values in the returned dict are mm unless suffixed Cm.
    """
    p = {}
    dd: adsk.core.DropDownCommandInput = inputs.itemById(BATTERY_TYPE_ID)
    p['battery'] = dd.selectedItem.name
    p['isRound'] = batteryDefs.BATTERY_DEFAULTS[p['battery']]['isRound']

    def mm(inputId):
        return adsk.core.ValueCommandInput.cast(inputs.itemById(inputId)).value * 10.0

    p['binX'] = adsk.core.IntegerSpinnerCommandInput.cast(inputs.itemById(BIN_WIDTH_ID)).value
    p['binY'] = adsk.core.IntegerSpinnerCommandInput.cast(inputs.itemById(BIN_LENGTH_ID)).value
    p['autoHeight'] = adsk.core.BoolValueCommandInput.cast(inputs.itemById(AUTO_HEIGHT_ID)).value

    p['slotDiaLen'] = mm(SLOT_DIA_LEN_ID)
    p['slotWidth'] = mm(SLOT_WIDTH_ID)
    p['slotDepth'] = mm(SLOT_DEPTH_ID)
    p['tipDiaLen'] = mm(TIP_DIA_LEN_ID)
    p['tipWidth'] = mm(TIP_WIDTH_ID)
    p['tipDepth'] = mm(TIP_DEPTH_ID)
    p['ledgeDrop'] = mm(LEDGE_DROP_ID)
    p['batteryLength'] = mm(BATTERY_LENGTH_ID)

    p['minSpacing'] = mm(MIN_SPACING_ID)
    p['wallClearance'] = mm(WALL_CLEARANCE_ID)
    p['ledgeFillet'] = mm(LEDGE_FILLET_ID)
    p['headroom'] = mm(HEADROOM_ID)
    p['baseDipAllowance'] = mm(BASE_DIP_ID)

    p['withLip'] = adsk.core.BoolValueCommandInput.cast(inputs.itemById(WITH_LIP_ID)).value
    p['lipNotches'] = adsk.core.BoolValueCommandInput.cast(inputs.itemById(LIP_NOTCHES_ID)).value
    p['wallThickness'] = mm(WALL_THICKNESS_ID)
    p['screwHoles'] = adsk.core.BoolValueCommandInput.cast(inputs.itemById(SCREW_HOLES_ID)).value
    p['screwDiameter'] = mm(SCREW_DIAMETER_ID)
    p['magnetCutouts'] = adsk.core.BoolValueCommandInput.cast(inputs.itemById(MAGNET_CUTOUTS_ID)).value
    p['magnetDiameter'] = mm(MAGNET_DIAMETER_ID)
    p['magnetDepth'] = mm(MAGNET_DEPTH_ID)

    p['baseWidthUnit'] = mm(BASE_WIDTH_UNIT_ID)
    p['baseLengthUnit'] = mm(BASE_LENGTH_UNIT_ID)
    p['heightUnitMm'] = mm(HEIGHT_UNIT_ID)
    p['xyClearance'] = mm(XY_CLEARANCE_ID)

    # the logo is not a dialog option - every bin carries it, always.
    # everything about it is fixed in lib/batteryUtils/logoUtils.py
    p['logoPath'] = BUNDLED_LOGO_PATH
    p['logoPlacement'] = logoUtils.LOGO_PLACEMENT
    p['logoSize'] = logoUtils.LOGO_SIZE
    p['logoDepth'] = logoUtils.LOGO_DEPTH
    p['logoRotation'] = logoUtils.LOGO_ROTATION
    p['logoMirror'] = logoUtils.LOGO_MIRROR

    errors = []
    warnings = []

    # height (in gridfinity units)
    baseHeightMm = const.BIN_BASE_HEIGHT * 10.0
    autoUnits = layout.autoMinHeightUnits(
        p['ledgeDrop'], p['slotDepth'], p['tipDepth'], p['baseDipAllowance'],
        p['heightUnitMm'], baseHeightMm)
    heightSpinner = adsk.core.IntegerSpinnerCommandInput.cast(inputs.itemById(BIN_HEIGHT_ID))
    if p['autoHeight']:
        p['units'] = autoUnits
    else:
        p['units'] = heightSpinner.value
    p['autoUnits'] = autoUnits

    # outer body + floor dimensions
    p['bodyW'] = p['baseWidthUnit'] * p['binX'] - 2.0 * p['xyClearance']
    p['bodyL'] = p['baseLengthUnit'] * p['binY'] - 2.0 * p['xyClearance']
    p['floorW'] = p['bodyW'] - 2.0 * p['wallThickness']
    p['floorL'] = p['bodyL'] - 2.0 * p['wallThickness']

    # slot layout
    if p['isRound']:
        p['layout'] = layout.computeRoundLayout(
            p['floorW'], p['floorL'], p['slotDiaLen'],
            p['minSpacing'], p['wallClearance'])
    else:
        p['layout'] = layout.computeRectLayout(
            p['floorW'], p['floorL'], p['slotDiaLen'], p['slotWidth'],
            p['minSpacing'], p['wallClearance'])

    # vertical stack-up
    p['fit'] = layout.fitCheck(
        p['units'], p['ledgeDrop'], p['slotDepth'], p['tipDepth'],
        p['batteryLength'], p['headroom'], p['heightUnitMm'], baseHeightMm)

    if p['layout'] is None:
        errors.append('No slot fits this bin size with the current clearances.')
    if p['slotDepth'] <= 0 or p['slotDiaLen'] <= 0:
        errors.append('Slot dimensions must be positive.')
    if not p['isRound'] and p['slotWidth'] <= 0:
        errors.append('Slot width must be positive for 9V.')
    if p['isRound'] and p['tipDiaLen'] >= p['slotDiaLen']:
        errors.append('Tip recess diameter must be smaller than the slot diameter.')
    if not p['isRound'] and (p['tipDiaLen'] >= p['slotDiaLen'] or p['tipWidth'] >= p['slotWidth']):
        errors.append('Tip recess must be smaller than the slot in both directions.')
    if p['ledgeDrop'] <= p['ledgeFillet']:
        errors.append('Ledge drop must be larger than the ledge fillet radius.')
    if p['ledgeFillet'] > p['wallClearance']:
        warnings.append('Ledge fillet radius exceeds the slot-to-wall clearance; '
                        'the fillet may run into the slots.')
    if p['fit']['margin'] < -1e-6:
        protrusion = p['batteryLength'] - p['ledgeDrop'] - p['slotDepth']
        if protrusion > 0:
            warnings.append('Battery would stand {:.1f} mm ABOVE the wall top - the bin '
                            'will not stack with batteries in it. Increase ledge drop '
                            'or slot depth by at least {:.1f} mm.'.format(
                                protrusion, protrusion + p['headroom']))
        else:
            warnings.append('Battery top is within {:.1f} mm of the wall top '
                            '(wanted {:.1f} mm of headroom).'.format(
                                -protrusion, p['headroom']))
    if not p['autoHeight'] and p['fit']['baseDip'] > p['baseDipAllowance'] + 1e-6:
        warnings.append('Slots reach {:.1f} mm into the base studs (allowance {:.1f} mm). '
                        'Increase bin height to at least {} u.'.format(
                            p['fit']['baseDip'], p['baseDipAllowance'], autoUnits))

    if not os.path.isfile(p['logoPath']):
        errors.append('The bundled logo is missing from the add-in (expected '
                      'resources/logo.svg); reinstall the add-in to restore it.')
    maxLogo = logoUtils.maxLogoWidth(p['baseWidthUnit'], p['xyClearance'])
    if p['logoSize'] > maxLogo + 1e-6:
        warnings.append('Logo is {:.1f} mm but a foot only offers {:.1f} mm of flat face; '
                        'the edges will run into the foot chamfer.'.format(p['logoSize'], maxLogo))

    p['errors'] = errors
    p['warnings'] = warnings
    return p


def formatResultText(p):
    lines = []
    if p['layout'] is not None:
        lines.append('<b>{}: {} batteries</b> ({})'.format(
            p['battery'], p['layout']['count'], p['layout']['desc']))
    else:
        lines.append('<b>{}: no batteries fit</b>'.format(p['battery']))
    totalH = p['units'] * p['heightUnitMm']
    lines.append('Bin {}x{}x{} u  =  {:.1f} x {:.1f} x {:.1f} mm'.format(
        p['binX'], p['binY'], p['units'], p['bodyW'], p['bodyL'], totalH))
    f = p['fit']
    lines.append('Wall top {:.1f} / ledge {:.1f} / slot bottom {:.1f} / recess {:.1f} mm'.format(
        f['wallTop'], f['ledgeZ'], f['slotBottomZ'], f['recessBottomZ']))
    if f['margin'] >= -1e-6:
        lines.append('Stackable: battery top {:.1f} mm, {:.1f} mm below wall top'.format(
            f['batteryTop'], f['wallTop'] - f['batteryTop']))
    if not p['errors']:
        lines.append('Logo engraved on the {}: {:.0f} mm, {:.1f} mm deep'.format(
            p['logoPlacement'].lower(), p['logoSize'], p['logoDepth']))
    for w in p['warnings']:
        lines.append('<font color="#aa5500"><b>Warning:</b> {}</font>'.format(w))
    for e in p['errors']:
        lines.append('<font color="#cc0000"><b>Error:</b> {}</font>'.format(e))
    return '<br>'.join(lines)


def updateComputed(inputs: adsk.core.CommandInputs):
    global _updatingInputs
    if _updatingInputs:
        return None
    _updatingInputs = True
    try:
        p = readParams(inputs)
        heightSpinner = adsk.core.IntegerSpinnerCommandInput.cast(inputs.itemById(BIN_HEIGHT_ID))
        heightSpinner.isEnabled = not p['autoHeight']
        if p['autoHeight'] and heightSpinner.value != p['units']:
            heightSpinner.value = p['units']
        resultText = adsk.core.TextBoxCommandInput.cast(inputs.itemById(RESULT_TEXT_ID))
        resultText.formattedText = formatResultText(p)
        return p
    except Exception:
        futil.log(f'{CMD_NAME} updateComputed failed, {getErrorMessage()}')
        return None
    finally:
        _updatingInputs = False


# ------------------------------------------------------------------ command UI
def command_created(args: adsk.core.CommandCreatedEventArgs):
    futil.log(f'{CMD_NAME} Command Created Event')
    inputs = args.command.commandInputs
    args.command.isExecutedWhenPreEmpted = False

    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)

    # info
    infoGroup = inputs.addGroupCommandInput(INFO_GROUP_ID, 'Info')
    infoGroup.isExpanded = False
    infoGroup.children.addTextBoxCommandInput(INFO_TEXT_ID, '', INFO_TEXT, 6, True)

    # battery
    batteryGroup = inputs.addGroupCommandInput(BATTERY_GROUP_ID, 'Battery')
    dd = batteryGroup.children.addDropDownCommandInput(
        BATTERY_TYPE_ID, 'Battery type', adsk.core.DropDownStyles.TextListDropDownStyle)
    for t in batteryDefs.BATTERY_TYPES:
        dd.listItems.add(t, t == 'AA', '')

    # bin size
    sizeGroup = inputs.addGroupCommandInput(SIZE_GROUP_ID, 'Bin size')
    sizeGroup.children.addIntegerSpinnerCommandInput(BIN_WIDTH_ID, 'Bin width, X (u)', 1, 20, 1, 2)
    sizeGroup.children.addIntegerSpinnerCommandInput(BIN_LENGTH_ID, 'Bin length, Y (u)', 1, 20, 1, 3)
    sizeGroup.children.addBoolValueInput(AUTO_HEIGHT_ID, 'Auto height (minimum for battery)', True, '', True)
    heightSpinner = sizeGroup.children.addIntegerSpinnerCommandInput(BIN_HEIGHT_ID, 'Bin height, Z (u)', 1, 50, 1, 8)
    heightSpinner.isEnabled = False

    # slot dimensions
    slotGroup = inputs.addGroupCommandInput(SLOT_GROUP_ID, 'Slot dimensions')
    addMmInput(slotGroup.children, SLOT_DIA_LEN_ID, 'Slot diameter / length', 14.75)
    addMmInput(slotGroup.children, SLOT_WIDTH_ID, 'Slot width (9V)', 0.0)
    addMmInput(slotGroup.children, SLOT_DEPTH_ID, 'Slot depth', 36.0)
    addMmInput(slotGroup.children, TIP_DIA_LEN_ID, 'Tip recess diameter / length', 6.0)
    addMmInput(slotGroup.children, TIP_WIDTH_ID, 'Tip recess width (9V)', 0.0)
    addMmInput(slotGroup.children, TIP_DEPTH_ID, 'Tip recess depth', 2.5)
    addMmInput(slotGroup.children, LEDGE_DROP_ID, 'Ledge drop (from wall top)', 15.0)
    addMmInput(slotGroup.children, BATTERY_LENGTH_ID, 'Battery overall length', 50.5)

    # layout rules
    rulesGroup = inputs.addGroupCommandInput(RULES_GROUP_ID, 'Layout rules')
    rulesGroup.isExpanded = False
    addMmInput(rulesGroup.children, MIN_SPACING_ID, 'Min distance between slots', batteryDefs.DEFAULT_MIN_SLOT_SPACING)
    addMmInput(rulesGroup.children, WALL_CLEARANCE_ID, 'Min distance slot to wall', batteryDefs.DEFAULT_MIN_WALL_CLEARANCE)
    addMmInput(rulesGroup.children, LEDGE_FILLET_ID, 'Ledge-to-wall fillet radius', batteryDefs.DEFAULT_LEDGE_FILLET_RADIUS)
    addMmInput(rulesGroup.children, HEADROOM_ID, 'Battery headroom below wall top', batteryDefs.DEFAULT_HEADROOM)
    addMmInput(rulesGroup.children, BASE_DIP_ID, 'Allowed cut into base studs', batteryDefs.DEFAULT_BASE_DIP_ALLOWANCE)

    # bin features
    featuresGroup = inputs.addGroupCommandInput(FEATURES_GROUP_ID, 'Bin features')
    featuresGroup.isExpanded = False
    featuresGroup.children.addBoolValueInput(WITH_LIP_ID, 'Stacking lip', True, '', True)
    featuresGroup.children.addBoolValueInput(LIP_NOTCHES_ID, 'Lip notches', True, '', False)
    addMmInput(featuresGroup.children, WALL_THICKNESS_ID, 'Wall thickness', const.BIN_LIP_WALL_THICKNESS * 10.0)
    featuresGroup.children.addBoolValueInput(SCREW_HOLES_ID, 'Screw holes', True, '', False)
    addMmInput(featuresGroup.children, SCREW_DIAMETER_ID, 'Screw hole diameter', const.DIMENSION_SCREW_HOLE_DIAMETER * 10.0)
    featuresGroup.children.addBoolValueInput(MAGNET_CUTOUTS_ID, 'Magnet cutouts', True, '', False)
    addMmInput(featuresGroup.children, MAGNET_DIAMETER_ID, 'Magnet cutout diameter', const.DIMENSION_MAGNET_CUTOUT_DIAMETER * 10.0)
    addMmInput(featuresGroup.children, MAGNET_DEPTH_ID, 'Magnet cutout depth', const.DIMENSION_MAGNET_CUTOUT_DEPTH * 10.0)

    # advanced gridfinity sizes
    advancedGroup = inputs.addGroupCommandInput(ADVANCED_GROUP_ID, 'Advanced (gridfinity sizes)')
    advancedGroup.isExpanded = False
    addMmInput(advancedGroup.children, BASE_WIDTH_UNIT_ID, 'Base width unit', const.DIMENSION_DEFAULT_WIDTH_UNIT * 10.0)
    addMmInput(advancedGroup.children, BASE_LENGTH_UNIT_ID, 'Base length unit', const.DIMENSION_DEFAULT_WIDTH_UNIT * 10.0)
    addMmInput(advancedGroup.children, HEIGHT_UNIT_ID, 'Bin height unit', const.DIMENSION_DEFAULT_HEIGHT_UNIT * 10.0)
    addMmInput(advancedGroup.children, XY_CLEARANCE_ID, 'Bin xy clearance', const.BIN_XY_CLEARANCE * 10.0)

    # preview + result
    previewGroup = inputs.addGroupCommandInput(PREVIEW_GROUP_ID, 'Preview')
    previewGroup.children.addBoolValueInput(SHOW_PREVIEW_ID, 'Show preview (slower)', True, '', False)
    inputs.addTextBoxCommandInput(RESULT_TEXT_ID, '', '', 7, True)

    applyBatteryDefaults(inputs)
    updateComputed(inputs)


def allCommandInputs(args):
    """Resolve the command's FULL input collection. In the inputChanged (and
    validate) events, args.inputs cannot be trusted to reach inputs that live
    in other groups, so itemById would silently return None; the command
    object itself always has the complete collection."""
    try:
        cmd = adsk.core.Command.cast(args.firingEvent.sender)
        if cmd and cmd.commandInputs:
            return cmd.commandInputs
    except Exception:
        pass
    return args.inputs


def command_input_changed(args: adsk.core.InputChangedEventArgs):
    global _updatingInputs
    if _updatingInputs:
        return
    inputs = allCommandInputs(args)
    try:
        if args.input.id == BATTERY_TYPE_ID:
            _updatingInputs = True
            try:
                applyBatteryDefaults(inputs)
            finally:
                _updatingInputs = False
        updateComputed(inputs)
    except Exception:
        futil.log(f'{CMD_NAME} input_changed failed, {getErrorMessage()}')


def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    try:
        p = readParams(allCommandInputs(args))
        args.areInputsValid = len(p['errors']) == 0
    except Exception:
        futil.log(f'{CMD_NAME} validate failed, {getErrorMessage()}')
        args.areInputsValid = False


def command_preview(args: adsk.core.CommandEventArgs):
    inputs = args.command.commandInputs
    showPreview = adsk.core.BoolValueCommandInput.cast(inputs.itemById(SHOW_PREVIEW_ID)).value
    if showPreview:
        args.isValidResult = generateBatteryBin(args)
    else:
        args.isValidResult = False


def command_execute(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Execute Event')
    generateBatteryBin(args)


def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    local_handlers = []
    futil.log(f'{CMD_NAME} Command Destroy Event')


# --------------------------------------------------------------- logo engraving
class LogoError(Exception):
    """Raised when the artwork itself is the problem, so the message shown to
    the user talks about the SVG rather than about Fusion."""


def curve3dBounds(curve3d):
    """(minX, minY, maxX, maxY) of a Curve3D.

    Goes through the curve's evaluator so lines, arcs, ellipses and splines
    are all measured the same way - an imported logo can contain any of them.
    """
    try:
        evaluator = curve3d.evaluator
        (ok, startParam, endParam) = evaluator.getParameterExtents()
        if not ok:
            return None
        (ok, points) = evaluator.getStrokes(startParam, endParam, 0.01)
        if not ok or not points:
            return None
        xs = [point.x for point in points]
        ys = [point.y for point in points]
        return (min(xs), min(ys), max(xs), max(ys))
    except Exception:
        return None


def unionBounds(boxes):
    boxes = [box for box in boxes if box]
    if not boxes:
        return None
    return (min(box[0] for box in boxes), min(box[1] for box in boxes),
            max(box[2] for box in boxes), max(box[3] for box in boxes))


def sketchCurveBounds(sketch: adsk.fusion.Sketch):
    return unionBounds([curve3dBounds(curve.geometry) for curve in sketch.sketchCurves])


def profileOuterBounds(profile: adsk.fusion.Profile):
    boxes = []
    for loop in profile.profileLoops:
        if not loop.isOuter:
            continue
        for profileCurve in loop.profileCurves:
            boxes.append(curve3dBounds(profileCurve.geometry))
    return unionBounds(boxes)


def importLogoSketch(component: adsk.fusion.Component, plane, svgPath, scale, name,
                     originX=0.0, originY=0.0):
    """Import the SVG into a new sketch at the given sketch-space offset.

    Position is set at import time on purpose. Fusion brings SVG geometry in
    as fixed curves, so Sketch.move quietly refuses to shift them afterwards -
    which leaves the artwork off the model and the cut with nothing to remove.
    """
    sketch = component.sketches.add(plane)
    sketch.name = name
    if not sketch.importSVG(svgPath, originX, originY, scale):
        sketch.deleteMe()
        raise LogoError('Fusion could not import this SVG. It needs real paths - '
                        'any lettering must be converted to outlines first.')
    return sketch


def measureImportedLogo(component, plane, svgPath, scale):
    """Import once into a throwaway sketch and report the bounding box."""
    probe = importLogoSketch(component, plane, svgPath, scale, 'Logo probe')
    bounds = sketchCurveBounds(probe)
    probe.deleteMe()
    return bounds


def engraveLogo(component: adsk.fusion.Component, binBody, p, CM):
    """Cut the logo into the flat bottom face of the chosen gridfinity foot.

    The sketch sits on the printed bottom face and the cut runs upwards into
    the foot, so the mark is always recessed - a raised logo would hold the
    bin off the build plate and off a baseplate.
    """
    svgPath = logoUtils.orientedSvgPath(p['logoPath'], p['logoMirror'],
                                        p['logoRotation'], tempfile.gettempdir())

    planeInput: adsk.fusion.ConstructionPlaneInput = component.constructionPlanes.createInput()
    planeInput.setByOffset(component.xYConstructionPlane,
                           adsk.core.ValueInput.createByReal(logoUtils.bottomZ() * CM))
    logoPlane = component.constructionPlanes.add(planeInput)
    logoPlane.name = 'Logo plane'

    # measure the artwork at 1:1 first - an SVG's own units tell us nothing
    # about how big Fusion will draw it, so scale is derived from what lands
    rawBounds = measureImportedLogo(component, logoPlane, svgPath, 1.0)
    if rawBounds is None:
        raise LogoError('The SVG produced no curves Fusion could measure.')
    rawSize = max(rawBounds[2] - rawBounds[0], rawBounds[3] - rawBounds[1])
    if rawSize <= 1e-9:
        raise LogoError('The SVG artwork has no size.')
    scale = (p['logoSize'] * CM) / rawSize

    # measure again at the real scale to learn exactly where an import lands,
    # so the final one can be offset straight onto the foot
    scaledBounds = measureImportedLogo(component, logoPlane, svgPath, scale)
    if scaledBounds is None:
        raise LogoError('The scaled SVG produced no curves.')
    scaledCenterX = (scaledBounds[0] + scaledBounds[2]) / 2.0
    scaledCenterY = (scaledBounds[1] + scaledBounds[3]) / 2.0

    centers = logoUtils.footCenters(p['binX'], p['binY'], p['baseWidthUnit'],
                                    p['baseLengthUnit'], p['xyClearance'],
                                    p['logoPlacement'])
    extrudeFeatures: adsk.fusion.ExtrudeFeatures = component.features.extrudeFeatures
    tolerance = 0.01  # cm; 0.1 mm is far tighter than any visible misplacement

    for index, (centerX, centerY) in enumerate(centers):
        name = 'Logo' if len(centers) == 1 else 'Logo {}'.format(index + 1)
        targetX = centerX * CM
        targetY = centerY * CM
        sketch = importLogoSketch(component, logoPlane, svgPath, scale, name,
                                  targetX - scaledCenterX, targetY - scaledCenterY)

        placedBounds = sketchCurveBounds(sketch)
        if placedBounds is None:
            raise LogoError('The scaled SVG produced no curves.')
        errorX = targetX - (placedBounds[0] + placedBounds[2]) / 2.0
        errorY = targetY - (placedBounds[1] + placedBounds[3]) / 2.0

        if abs(errorX) > tolerance or abs(errorY) > tolerance:
            # import offset did not behave as a plain translation; try nudging
            # the curves instead, then insist on the result rather than
            # cutting thin air the way a silent miss would
            move = adsk.core.Matrix3D.create()
            move.translation = adsk.core.Vector3D.create(errorX, errorY, 0)
            sketch.move(commonUtils.objectCollectionFromList(
                [curve for curve in sketch.sketchCurves]), move)
            placedBounds = sketchCurveBounds(sketch)
            errorX = targetX - (placedBounds[0] + placedBounds[2]) / 2.0
            errorY = targetY - (placedBounds[1] + placedBounds[3]) / 2.0
            if abs(errorX) > tolerance or abs(errorY) > tolerance:
                raise LogoError(
                    'The logo could not be positioned on the foot - it landed '
                    '{:.1f} mm / {:.1f} mm away from the target.'.format(
                        errorX / CM, errorY / CM))

        profiles = [profile for profile in sketch.profiles]
        if not profiles:
            raise LogoError('The SVG has no closed shapes to engrave - every path that '
                            'should be cut has to form a closed loop.')
        boxes = [profileOuterBounds(profile) for profile in profiles]
        if any(box is None for box in boxes):
            regions = profiles
        else:
            regions = [profiles[i] for i in logoUtils.keepByNestingParity(boxes)]
        if not regions:
            raise LogoError('Every region in the SVG looked like a hole; check the artwork.')

        cutInput = extrudeFeatures.createInput(
            commonUtils.objectCollectionFromList(regions),
            adsk.fusion.FeatureOperations.CutFeatureOperation)
        cutInput.participantBodies = [binBody]
        # Symmetric rather than one-sided: the sketch plane is offset DOWNWARDS
        # to the printed face, and a one-sided cut depends on which way that
        # plane's normal ends up pointing. Cutting the same depth either side
        # takes the material above the face and harmlessly sweeps air below,
        # so the engraving is the right depth whichever way the normal faces.
        cutInput.setSymmetricExtent(
            adsk.core.ValueInput.createByReal(p['logoDepth'] * CM * 2.0), True)
        extrudeFeatures.add(cutInput).name = name + ' engrave'


# ------------------------------------------------------------------ generation
def generateBatteryBin(args: adsk.core.CommandEventArgs):
    try:
        inputs = args.command.commandInputs
        p = readParams(inputs)
        if p['errors']:
            args.executeFailed = True
            args.executeFailedMessage = '<br>'.join(p['errors'])
            return False

        des = adsk.fusion.Design.cast(app.activeProduct)
        if des.designType == adsk.fusion.DesignTypes.DirectDesignType:
            raise UnsupportedDesignTypeException(
                'Timeline must be enabled for the generator to work')
        root = adsk.fusion.Component.cast(des.rootComponent)

        # mm -> cm (Fusion internal units)
        CM = 0.1
        baseWidth = p['baseWidthUnit'] * CM
        baseLength = p['baseLengthUnit'] * CM
        heightUnit = p['heightUnitMm'] * CM
        xyClearance = p['xyClearance'] * CM
        wall = p['wallThickness'] * CM
        binX, binY, units = p['binX'], p['binY'], p['units']

        binName = 'Battery bin {} {}x{}x{} ({} cells)'.format(
            p['battery'], binX, binY, units, p['layout']['count'])

        originalTimelineCount = des.timeline.count
        if des.designIntent == adsk.fusion.DesignIntentTypes.HybridDesignIntentType:
            newCmpOcc = adsk.fusion.Occurrences.cast(root.occurrences).addNewComponent(adsk.core.Matrix3D.create())
            newCmpOcc.component.name = binName
            newCmpOcc.activate()
            component: adsk.fusion.Component = newCmpOcc.component
        else:
            component: adsk.fusion.Component = root

        # ---- gridfinity base (studs)
        baseInput = BaseGeneratorInput()
        baseInput.originPoint = geometryUtils.createOffsetPoint(
            component.originConstructionPoint.geometry,
            byX=-xyClearance,
            byY=-xyClearance,
        )
        baseInput.baseWidth = baseWidth
        baseInput.baseLength = baseLength
        baseInput.xyClearance = xyClearance
        baseInput.hasScrewHoles = p['screwHoles']
        baseInput.hasMagnetCutouts = p['magnetCutouts']
        baseInput.hasMagnetCutoutsTabs = False
        baseInput.screwHolesDiameter = p['screwDiameter'] * CM
        baseInput.magnetCutoutsDiameter = p['magnetDiameter'] * CM
        baseInput.magnetCutoutsDepth = p['magnetDepth'] * CM
        baseBodies = createBaseBodyPattern(baseInput, binX, binY, component)

        # ---- solid bin body with stacking lip
        bodyInput = BinBodyGeneratorInput()
        bodyInput.hasLip = p['withLip']
        bodyInput.hasLipNotches = p['lipNotches']
        bodyInput.binWidth = binX
        bodyInput.binLength = binY
        bodyInput.binHeight = units
        bodyInput.baseWidth = baseWidth
        bodyInput.baseLength = baseLength
        bodyInput.heightUnit = heightUnit
        bodyInput.xyClearance = xyClearance
        bodyInput.binCornerFilletRadius = const.BIN_CORNER_FILLET_RADIUS - xyClearance
        bodyInput.isSolid = True
        bodyInput.wallThickness = wall
        bodyInput.hasScoop = False
        bodyInput.hasTab = False
        binBody = createGridfinityBinBody(bodyInput, component)

        cutBaseClearance(baseInput, binX, binY, component)

        # merge base into body (binBody stays the combine target)
        toolBodies = commonUtils.objectCollectionFromList(baseBodies)
        combineUtils.joinBodies(binBody, toolBodies, component)

        bodyW = p['bodyW'] * CM
        bodyL = p['bodyL'] * CM
        baseHeightMm = const.BIN_BASE_HEIGHT * 10.0
        wallTopCm = layout.bodyTopHeight(units, p['heightUnitMm'], baseHeightMm) * CM
        ledgeZCm = wallTopCm - p['ledgeDrop'] * CM

        # ---- interior pocket down to the ledge, with the ledge-to-wall fillet
        pocketInput = BinBodyCutoutGeneratorInput()
        pocketInput.origin = adsk.core.Point3D.create(wall, wall, wallTopCm)
        pocketInput.width = bodyW - 2.0 * wall
        pocketInput.length = bodyL - 2.0 * wall
        pocketInput.height = p['ledgeDrop'] * CM
        pocketInput.hasScoop = False
        pocketInput.filletRadius = p['ledgeFillet'] * CM
        pocketInput.hasBottomFillet = True
        pocketBody = createGridfinityBinBodyCutout(pocketInput, component)
        combineUtils.cutBody(binBody, commonUtils.objectCollectionFromList([pocketBody]), component)

        # ---- battery slots
        centers = p['layout']['centers']  # mm, relative to pocket lower-left corner
        planeInput: adsk.fusion.ConstructionPlaneInput = component.constructionPlanes.createInput()
        planeInput.setByOffset(component.xYConstructionPlane, adsk.core.ValueInput.createByReal(ledgeZCm))
        ledgePlane = component.constructionPlanes.add(planeInput)
        ledgePlane.name = 'Battery slot plane'

        slotSketch: adsk.fusion.Sketch = component.sketches.add(ledgePlane)
        slotSketch.name = 'Battery slots'
        slotSketch.isComputeDeferred = True
        if p['isRound']:
            radius = p['slotDiaLen'] * CM / 2.0
            for (cx, cy) in centers:
                slotSketch.sketchCurves.sketchCircles.addByCenterRadius(
                    adsk.core.Point3D.create(wall + cx * CM, wall + cy * CM, 0), radius)
        else:
            sx = p['layout']['slotX'] * CM
            sy = p['layout']['slotY'] * CM
            for (cx, cy) in centers:
                x = wall + cx * CM
                y = wall + cy * CM
                slotSketch.sketchCurves.sketchLines.addTwoPointRectangle(
                    adsk.core.Point3D.create(x - sx / 2.0, y - sy / 2.0, 0),
                    adsk.core.Point3D.create(x + sx / 2.0, y + sy / 2.0, 0))
        slotSketch.isComputeDeferred = False
        slotProfiles = commonUtils.objectCollectionFromList(list(slotSketch.profiles))
        slotExtrude = adsk.fusion.ExtrudeFeatures.cast(component.features.extrudeFeatures)
        slotCutInput = slotExtrude.createInput(slotProfiles, adsk.fusion.FeatureOperations.CutFeatureOperation)
        slotCutInput.participantBodies = [binBody]
        slotCutInput.setOneSideExtent(
            adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(p['slotDepth'] * CM)),
            adsk.fusion.ExtentDirections.NegativeExtentDirection,
            adsk.core.ValueInput.createByReal(0))
        slotExtrude.add(slotCutInput).name = 'Battery slot cuts'

        # ---- tip recesses (button never carries the battery weight)
        tipSketch: adsk.fusion.Sketch = component.sketches.add(ledgePlane)
        tipSketch.name = 'Battery tip recesses'
        tipSketch.isComputeDeferred = True
        if p['isRound']:
            radius = p['tipDiaLen'] * CM / 2.0
            for (cx, cy) in centers:
                tipSketch.sketchCurves.sketchCircles.addByCenterRadius(
                    adsk.core.Point3D.create(wall + cx * CM, wall + cy * CM, 0), radius)
        else:
            rotated = p['layout']['slotX'] < p['layout']['slotY']
            tx = (p['tipWidth'] if rotated else p['tipDiaLen']) * CM
            ty = (p['tipDiaLen'] if rotated else p['tipWidth']) * CM
            for (cx, cy) in centers:
                x = wall + cx * CM
                y = wall + cy * CM
                tipSketch.sketchCurves.sketchLines.addTwoPointRectangle(
                    adsk.core.Point3D.create(x - tx / 2.0, y - ty / 2.0, 0),
                    adsk.core.Point3D.create(x + tx / 2.0, y + ty / 2.0, 0))
        tipSketch.isComputeDeferred = False
        tipProfiles = commonUtils.objectCollectionFromList(list(tipSketch.profiles))
        tipCutInput = slotExtrude.createInput(tipProfiles, adsk.fusion.FeatureOperations.CutFeatureOperation)
        tipCutInput.participantBodies = [binBody]
        tipCutInput.setOneSideExtent(
            adsk.fusion.DistanceExtentDefinition.create(
                adsk.core.ValueInput.createByReal((p['slotDepth'] + p['tipDepth']) * CM)),
            adsk.fusion.ExtentDirections.NegativeExtentDirection,
            adsk.core.ValueInput.createByReal(0))
        slotExtrude.add(tipCutInput).name = 'Battery tip recess cuts'

        # ---- logo engraved into the printed bottom face (always)
        engraveLogo(component, binBody, p, CM)

        binBody.name = binName

        binGroup = des.timeline.timelineGroups.add(originalTimelineCount, des.timeline.count - 1)
        binGroup.name = binName
    except UnsupportedDesignTypeException:
        args.executeFailed = True
        args.executeFailedMessage = ('Design type is unsupported. Projects with disabled design '
                                     'history are unsupported, please enable timeline to proceed.')
        return False
    except LogoError as err:
        args.executeFailed = True
        args.executeFailedMessage = ('The logo could not be engraved: {}<br>The artwork lives at '
                                     'commands/commandCreateBatteryBin/resources/logo.svg '
                                     'inside the add-in.'.format(err))
        futil.log(f'{CMD_NAME} Logo error, {err}')
        return False
    except Exception:
        args.executeFailed = True
        args.executeFailedMessage = getErrorMessage()
        futil.log(f'{CMD_NAME} Error occurred, {getErrorMessage()}')
        return False
    return True

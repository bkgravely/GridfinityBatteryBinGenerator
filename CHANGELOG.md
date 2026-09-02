# Changelog

## 1.1.1 — 2026-08-30

- New optional chemistry label tab: a triangular shelf across a corner of the
  ledge carrying a two or three letter code (ALK, LI, NMH, ION, RCH, ZNC, or
  your own through "Other"). Off by default. The battery size is not on it -
  you are looking into the bin to read it, so you can see that already - which
  keeps the shelf small.
- The shelf costs at most one slot, measured across every battery, every bin
  size from 1x2 to 5x5 and all four corners: 24 mm is the largest leg that never
  costs more than one anywhere. The shipped lettering height of 5.9 mm is the
  tallest that keeps every code in the list inside it - NMH is the binding one,
  and ALK lands at 22.5 mm. One battery out of twenty-five buys a label you can
  read across a drawer.
- The shelf is sized from a table of Arial Bold character widths rather than an
  average, because the average was wrong in a way that showed: at 0.68 cap
  heights per character "ALK" at 7.5 mm was taken for 15.3 mm wide when it is
  really 22.4 mm, so the triangle came out 5 mm short and the ends of the text
  ran 3.5 mm past the legs and surfaced inside the bin wall. Widths run from
  0.40 (I) to 1.37 (W), so which letters are in a code moves the shelf as much
  as how many: LI needs 15.4 mm of leg where NMH needs 23.9 mm. An unlisted
  character is sized as the widest there is, and a font other than Arial,
  Helvetica or Liberation Sans warns that the estimate does not apply to it.
- A smaller shelf costs nothing at all, and that part is a guarantee rather than
  a measurement: every slot keeps the wall clearance from both walls, so a
  corner triangle within twice that clearance cannot reach one. A free shelf
  that size holds a two-letter code at a printable stroke, but not a
  three-letter one. The readout states the cost and the stroke width either
  way, and warns past the one-slot size.
- The shelf is a wedge rather than a block: full thickness at the walls,
  tapering to the hypotenuse so the underside is at 45 degrees and prints
  without support, with its top 1 mm below the wall top so bins still stack.
  The lettering runs parallel to the hypotenuse, is set bold, and stands 0.4 mm
  proud as its own body, which still clears a stacked bin and lets the slicer
  give the text its own filament without painting layer by layer. Bold is not
  decoration: raised text prints as walls, and a regular weight at this size has
  stems around 0.34 mm, narrower than the line a 0.4 mm nozzle lays down. The
  slicer discards such a wall rather than thinning it, so the letters vanish and
  a blank shelf prints. The readout now states the stroke width, and the dialog
  warns when a text height would take it under 0.45 mm. That is also why it is on a
  horizontal face: on an outside wall a colour change would need a filament
  swap on every layer of the text.
- The lettering is joined into the bin, so a generated bin is one solid body
  and reaches the slicer as one object. It was built as separate bodies on
  purpose - a slicer assigns filament per part, so text arriving as its own
  part is the difference between picking it and hand-painting it - but that
  does not survive the export. Fusion writes one 3MF object per body and Bambu
  Studio loads those as separate objects rather than parts of one, dropping
  each to the plate: a labelled 2x3 came in as four objects, letters scattered
  across the bed with one off the plate entirely. A colour option is queued
  behind sorting that out; `JOIN_TEXT_TO_BIN` in the command switches the
  separate bodies back on.
- Added `tests/test_names.py`, a static check for names used but never bound.
  Most of the geometry code cannot run outside Fusion, so a deleted local
  survives every other test and only surfaces as a NameError in a dialog -
  which is exactly how two of them reached a build of this feature. It walks
  every function instead of running it, and understands closures so it does not
  cry wolf about nested helpers.
- The shelf overlaps the wall by a computed depth rather than a full wall
  thickness. A whole wall thickness put its square corner 1.55 mm outside the
  bin's filleted outer corner, which showed up as a tab hanging off the edge of
  every labelled bin. The safe depth follows from the fillet geometry, and the
  dialog warns when a wall is thin enough that no depth is safe.
- `layout.py` gained a convex exclusion zone, and round layouts now report
  per-slot footprints like rectangular ones do, so both go through the same
  code.

- Uninstalling no longer takes Autodesk\ApplicationPlugins with it. Windows
  Installer deletes any directory it created once the last thing in it is
  removed, so on a machine where this was the only add-in installed that way,
  removing it deleted the shared plugin folder and the Autodesk folder above it
  - leaving the next installer, or Autodesk itself, to find the path gone. Two
  permanent components now hold those two folders open; only the add-in's own
  folder is ours to remove. wixl does not implement Permanent and says so on
  stderr rather than failing, so the Linux build sets the bit afterwards and
  checks it took.

- Fixed the middle of the R filling in on the engraved logo, and the rule
  behind it. Regions are ink or counter by nesting depth - odd is a hole - and
  that depth was counted from bounding boxes, which say nothing about whether
  one shape really contains another. In the monogram the tree stands between
  the R and the C, so its box swallows the R's counter while containing none of
  it; the phantom level flipped the counter from hole to cut. Nesting now comes
  from the loops Fusion itself worked out: a region carries its holes as inner
  loops, and the region filling a hole has those same curves as its outer loop,
  so following that chain gives an exact depth. Boxes remain only as a fallback
  for artwork whose loops cannot be read. The old wordmark never hit this - its
  letters sit side by side, each box minding its own business.

- The engraving is 0.8 mm deep rather than 0.4. The bin prints logo-down, so
  the recess is a void and its floor is a layer laid across open air - it keeps
  the round profile of each extrusion instead of being squashed flat by the
  plate like the face around it, and nothing in a slicer makes an air-printed
  surface glassy (ironing only works on upward-facing ones). Depth does not
  change that, it changes how much of it you see: printed side by side, 0.4
  catches the light and shows every strand, 0.8 drops the floor into shadow and
  the mark reads as a cut. Bridge span follows the width of the strokes, not
  the depth, so the extra 0.4 mm costs nothing - and four 0.2 mm layers still
  lands on a layer boundary.

- New engraving artwork: the R / redwood / C monogram replaces the full
  wordmark. It reads as Redwood Craftworks without spelling it out, and it is
  a better fit for a 31 mm mark on a foot - the narrowest feature in it is a
  branch tip rather than the waist of an S. Measured against the wordmark it
  engraves nearly twice as heavy (median feature 1.43 mm against 0.79 mm) and
  halves the gap area too narrow for a 0.42 mm line, from 13.6% to 6.7%. The
  only detail that will not survive at this size is the hairline spike at the
  top of the tree; every branch, the trunk and both letters are clear of it.
  Same corner, same orientation, same 31 mm ceiling - the artwork is portrait,
  so that is now its height and the width comes out around 19 mm. The wordmark
  is kept at `docs/logo-wordmark.svg`.

- Fixed the two non-manifold edges slicers reported on bins built with 1.1.0.
  They came from the new logo artwork: two of its contours crossed themselves,
  and an outline that crosses itself extrudes into a non-manifold edge. The
  crossings were invisible - hairline stubs a thousandth of a millimetre long,
  left at the end of a contour by the drawing program, doubling back over their
  neighbour. Bins still sliced and printed, but every slicer flagged them.
- `tools/bake_logo.py` now repairs that class of defect rather than passing it
  through: it drops degenerate segments (below 0.05 SVG units, a hundredth of
  the smallest real feature), heals the gap that leaves instead of emitting a
  broken contour, and trims a tail that overshoots the start back to where it
  actually crosses.
- The tool now validates what it produced and refuses to write it if any
  contour is left open or self-intersecting, so this cannot ship unnoticed
  again. It also bakes before opening the output file - a failed run used to
  truncate logo.svg to nothing.
- No visible change to the engraving: the repaired artwork differs from 1.1.0's
  by 23 pixels in a million, all of them antialiasing along an edge.


## 1.1.0 — 2026-08-28

Minor rather than patch: bins regenerated with this version are not
dimensionally identical to 1.0.x ones. The 9V layout, the CR123 auto height and
the engraved logo all change.

- 9V slots are now packed in mixed orientations: the generator fills the strip
  a uniform grid leaves over with a row turned 90 degrees. A 3x3 bin holds 18
  instead of 15, a 2x3 holds 11 instead of 10, a 3x4 holds 26 instead of 25.
  New "Allow mixed slot orientations" checkbox, default ON, turns it off for a
  uniform grid; the readout then says how many cells that costs. The setting
  is hidden for round batteries, which have no orientation to mix.
- The 9V tip recess is 21 x 9 mm, measured with calipers rather than taken
  from a nominal figure. The old 14 x 8 recess did not clear the snap
  terminals. The battery still lands on a 3.2 mm shoulder at each end and
  4.25 mm down each side.
- Cuts must now leave a solid floor under them, 1 mm by default, replacing the
  old 0.5 mm allowance for dipping into the base. The dip was only ever safe
  where a recess happened to sit over a foot; the slot grid is centred on the
  bin and not aligned to the 42 mm foot pitch, so on a 2x3 CR123 bin four of
  the twenty recesses would have broken clean through the gap between feet.
  CR123 auto height moves from 6 u to 7 u as a result.
- New "Constrain height to gridfinity units" checkbox, default OFF. Gridfinity
  fixes the 42 mm footprint but not the height, so a bin can now be exactly as
  tall as its slots require instead of rounding up to the next 7 mm. Saves
  2.4 mm on AAA, 3.4 on AA, 5.4 on CR123, 4.0 on 9V and 2.4 on 18650.
- New "Round height to layer" input, 0.2 mm by default and shown only when the
  height is not constrained to units, so a free height lands on a whole print
  layer instead of part way through one. A manually typed height is never
  overridden, only flagged in the readout.
- The engraved logo grows from 28 mm to 31 mm, right at the ceiling a 35.1 mm
  foot allows with the 2 mm chamfer margin.
- New artwork, drawn with solid letterforms instead of outlined ones. The old
  logo cut its second line as grooves around 0.41 mm wide, which closed up
  under first-layer squish and cost the last letters on a print. Scaling alone
  could not fix that - 31.1 mm is all a foot has - so the letters are now solid
  shapes whose narrowest strokes measure 0.51 mm, clear of the roughly 0.5 mm
  floor a 0.4 mm nozzle can hold. Same wordmark, same 28 contours, same 9
  counters kept open by nesting parity.
- Added `tools/bake_logo.py`, which produces the bundled `logo.svg` from
  `docs/logo-source.svg`: it bakes the mirror and 90 degree rotation into the
  path data, drops zero-length segments, and snaps every contour shut. That
  preparation used to be a set of one-off commands; now it is a script in the
  repo, so replacing the artwork is one line.
- README documents the free-versus-unit height trade-off, the mixed 9V
  packing, and the floor rule, and credits Lev Mishin's
  FusionGridfinityGenerator v1.4.3.0 as the source of the bundled geometry
  library by version. Added a section on verifying a release download by
  SHA-256 and Authenticode signature.


## 1.0.8 — 2026-08-26

- The installer's Finish page now names the command correctly: "find Gridfinity
  Battery Bin under Solid - Create". That wording is generated from the add-in's
  own CMD_NAME, so renaming the command can no longer leave the installer
  telling people to look for something that isn't there.
- Replaced the stock WiX artwork with branded installer graphics: a blue-to-black
  panel carrying the gravlaxy logo, chosen so the red and gold mark stands out,
  with the logo's white stars preserved against the dark background.
- Added `installer/build-linux.sh` for reproducible msitools builds, and
  `make_wxs.py --wix` for the WiX Toolset path on Windows.


## 1.0.7 — 2026-08-26

- The Fusion command is now called "Gridfinity Battery Bin" in Solid > Create,
  rather than just "Battery bin".
- The Add/Remove Programs entry now shows the gravlaxy logo, built as a
  multi-resolution icon (16 through 256 px) with its transparency intact.


## 1.0.6 — 2026-08-26

- Rotated the logo 90 degrees so it sits upright on the foot, reading
  horizontally with the tree above the wordmark when the bin is turned over.
- Orientation is now baked into the artwork's path data instead of being
  applied at import. Fusion imports SVG geometry as fixed curves and clips to
  the viewBox, so a transform attribute is not something to depend on.
- Cleaned 35 zero-length segments out of the artwork and closed every contour
  exactly on its start point, so Fusion reliably forms a profile for each of
  the 28 regions.
- `wrapSvgTransform` now widens the viewBox and drops width/height when it
  applies a rotation or mirror, so swapped-in artwork is not clipped or
  squashed. The original artwork is kept at `docs/logo-source.svg`.


## 1.0.5 — 2026-08-26

- Fixed the logo never appearing on generated bins. Fusion imports SVG geometry
  as fixed curves, so moving it into place after import was silently ignored
  and the artwork stayed off the model, leaving the cut nothing to remove. The
  logo is now positioned at import time, its position is verified afterwards,
  and a miss raises a real error instead of failing quietly.
- The engraving cut is now symmetric about the bottom face, so it no longer
  depends on which way the offset construction plane's normal points.


## 1.0.4 — 2026-08-26

- The installer now has a UI: a licence page, a progress bar, and a Finish page
  that confirms the install succeeded and reminds you to restart Fusion.
  Previously it ran silently and gave no sign it had worked.
- Installer publisher reads "Bryan Gravely", matching the code-signing
  certificate, and the Add/Remove Programs entry links to the GitHub page.


## 1.0.3 — 2026-08-24

- Every bin is now branded: the Redwood Craftworks logo is engraved into the
  corner gridfinity foot, 28 mm across and 0.4 mm deep. It is deliberately not
  a dialog option — size, depth, foot and orientation are constants in
  `lib/batteryUtils/logoUtils.py` and the artwork is the bundled
  `resources/logo.svg`.
- The mark is always recessed: a raised one would hold the bin off the build
  plate and rock it on a baseplate.
- Nested regions are resolved by nesting depth, so counters in lettering stay
  open rather than filling in.
- Added a packaging test that fails if the version or publisher drifts between
  the manifest, PackageContents.xml and the WiX source.

## 1.0.2 — 2026-08-24

- Added 18650 battery type (19 mm slots, 51 mm deep, 10 mm tip recess for
  button tops, auto height 11 u). Defaults assume unprotected 65.2 mm cells;
  for protected/button-top cells raise battery length and slot depth in the
  dialog. A 2x3 bin holds 15; larger bins switch to hex packing automatically.

## 1.0.1 — 2026-08-24

- Fixed battery type switching not applying that battery's dimensions
  (Fusion `inputChanged` events cannot reliably reach inputs in other dialog
  groups; all handlers now resolve the full input collection from the command).
- Fixed 9V being unselectable (OK greyed out) for the same reason.
- Added a regression test simulating the Fusion input-collection quirk.

## 1.0.0 — 2026-08-24

- Initial release: AAA / AA / CR123 / 9V battery bins with maximized
  square/hex-offset slot layouts, tip recesses, auto height, stackability
  check, and editable layout rules. Gridfinity geometry via the bundled
  GridfinityGenerator library (CC BY-NC-SA 4.0, Lev Mishin).

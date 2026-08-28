# Changelog

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

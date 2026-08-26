# Changelog

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

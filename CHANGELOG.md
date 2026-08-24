# Changelog

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

# GridfinityBatteryBinGenerator — Fusion 360 add-in

Generates a gridfinity bin and cuts a maximized grid of tip-down battery
storage slots into it, in one dialog. Supports AAA, AA, CR123, and 9V.
The bin geometry (base studs, walls, stacking lip, magnet/screw options)
comes from the bundled GridfinityGenerator library, so bins match the ones
that plugin produces.

## Install

1. Copy the whole `GridfinityBatteryBinGenerator` folder to your Fusion add-ins folder:
   - Windows: `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\`
   - macOS: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/`
2. In Fusion: **Utilities → ADD-INS (Scripts and Add-Ins) → Add-Ins tab**,
   select **GridfinityBatteryBinGenerator**, check *Run on Startup*, click **Run**.
3. A **Battery bin** button appears in **Solid → Create** (next to where the
   Gridfinity bin button lives).

## Use

Pick a battery type and the bin footprint in gridfinity units (X × Y).
Everything else is prefilled from the proven dimension table and stays
editable:

- **Auto height** picks the minimum number of 7 mm height units that keeps
  the deepest cut (slot + tip recess) inside the bin (a small dip into the
  solid base studs is allowed, 0.5 mm by default). Untick it to force a
  height; the readout warns if the slots would outrun the bin.
- The **result box** at the bottom shows the battery count and layout
  (square vs hex-offset — whichever fits more), the vertical stack-up, and a
  stackability check: the battery's full length is kept below the wall top so
  a bin stacked on top never touches the batteries.
- **Ledge drop** is measured down from the top face of the bin walls (the
  solid bin's top). The interior is pocketed down that far, with a fillet
  (3 mm default) where the ledge meets the walls; the 5 mm slot-to-wall
  clearance guarantees the fillet never runs into a slot.
- Tip-down storage: every slot gets a recess at the bottom (diameter/depth
  per battery type) so the battery rests on its shoulder, never on the
  button. For 9V the slot and recess are rectangles covering both snap
  terminals; the grid rotates the slots if that fits more.
- **Show preview** regenerates the full bin on every input change — handy but
  slower on large bins; leave it off and just hit OK.

Default dimension table (editable in
`lib/batteryUtils/batteryDefs.py`, all mm):

| | AAA | AA | CR123 | 9V |
|---|---|---|---|---|
| Slot Ø / L×W | 11 | 14.75 | 17 | 27.4 × 17.5 |
| Slot depth | 30 | 36 | 20 | 34 |
| Tip recess Ø / L×W | 4 | 6 | 7 | 14 × 8 |
| Tip recess depth | 2.5 | 2.5 | 2.5 | 4 |
| Ledge drop | 15 | 15 | 15 | 15 |
| Battery length | 44.5 | 50.5 | 34.5 | 48.5 |
| Auto height | 8 u | 9 u | 6 u | 9 u |

Layout rules: ≥3 mm between slots (including hex diagonals), ≥5 mm from
slot to inner wall, pattern centered in the bin.

## Tests

`tests/` contains plain-Python tests that run without Fusion:

```
python3 tests/test_layout.py      # packing + height math
python3 tests/test_entry_sim.py   # dialog logic with a stubbed Fusion API
```

## License / attribution

Bundles the `gridfinityUtils` / `fusion360utils` libraries from
[FusionGridfinityGenerator](https://github.com/Le0Michine/FusionGridfinityGenerator)
by Lev Mishin, licensed under CC BY-NC-SA 4.0 (same license as Gridfinity by
Zack Freedman). This add-in therefore carries the same license:
non-commercial use, share-alike, with attribution.

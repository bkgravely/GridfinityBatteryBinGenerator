# Attribution

The `lib/gridfinityUtils`, `lib/fusion360utils`, `lib/ui`, and
`lib/configUtils.py` modules are vendored unmodified from
FusionGridfinityGenerator **v1.4.3.0** by Lev Mishin (Le0Michine):
https://github.com/Le0Michine/FusionGridfinityGenerator
https://github.com/Le0Michine/FusionGridfinityGenerator/releases/tag/v1.4.3.0

Every gridfinity feature this add-in produces - the base studs, the walls, the
stacking lip, the magnet and screw cutouts - is his geometry, called through
that library. This add-in adds the battery slots and the layout math on top.

That project, and therefore this add-in, is licensed under the
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
License (CC BY-NC-SA 4.0), the same license as the Gridfinity system by
Zack Freedman: https://creativecommons.org/licenses/by-nc-sa/4.0/

The battery slot layout logic (`lib/batteryUtils`) and the Battery bin
command (`commands/commandCreateBatteryBin`) were written for this add-in.

"""Scratch: print v6 campaign numbers."""
import seed_model as sm
import soft_shell as soft

soft_std = sm.quote("stem_cell")
hard_std = sm.quote("stem_cell", shell="hard")
geom = sm.seed_geometry()
print(f"soft standard: build={soft_std.cost_to_build:,.0f} "
      f"price={soft_std.price:,.0f} "
      f"per_sqft={soft_std.price / geom.floor_decagon_sqft:,.2f}")
print(f"hard standard: build={hard_std.cost_to_build:,.0f} "
      f"price={hard_std.price:,.0f}")
print(f"standard saving (list): {hard_std.price - soft_std.price:,.0f}")
print(f"cap stack: 0 layers={soft.soft_shell(0).cost:,.0f} "
      f"3 layers={soft.soft_shell(3).cost:,.0f} "
      f"7 layers={soft.soft_shell(7).cost:,.0f}")
hull_bays = (sm.shell_group(geom, "boatyard").cost
             + sm.envelope_group(geom).cost)
print(f"hull+bays = {hull_bays:,.0f}")
print()
print(sm.floating_report())
print()
print(soft.report()[:1500])

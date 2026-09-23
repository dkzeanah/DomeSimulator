"""Scratch: inspect the raw model's topology and mesh keys."""
from two_v_demo import raw_wedge_bridge as bridge

m = bridge.model()
sim = bridge.simulator()
print("meshes:", sorted(sim.build_world_meshes(m).keys()))
print("topology attrs:", [a for a in dir(m.topology) if not a.startswith("_")])
print("radius:", m.topology.sphere_radius_in)
verts = m.topology.vertices if hasattr(m.topology, "vertices") else None
print("vertices shape:", getattr(verts, "shape", None), "dtype:",
      getattr(verts, "dtype", None))
print("faces attr:", getattr(m.topology, "faces", None))

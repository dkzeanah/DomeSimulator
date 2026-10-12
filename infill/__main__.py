"""py -3.12 -m infill  -- the Triangle Infill 3-D cutting tool.
py -3.12 -m infill --selftest  -- check the geometry, every pattern, every recipe."""

import sys

if "--selftest" in sys.argv:
    from . import selftest
    raise SystemExit(selftest.run())

from .app3d import main

raise SystemExit(main())

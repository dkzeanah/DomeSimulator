"""Every check the infill calculator has, in one place."""


def run() -> int:
    from .frame import validate_frame
    from .patterns import validate_patterns
    from .section import validate_section
    validate_frame()
    print("frame ok")
    validate_section()
    print("section ok")
    validate_patterns()
    print("patterns ok")
    from .solids import validate_solids
    from .recipes import validate_recipes
    validate_solids()
    print("solids ok")
    validate_recipes()
    print("recipes ok")
    from .app3d import validate_meshes
    validate_meshes()
    print("3-D meshes ok")
    from .base import validate_base
    validate_base()
    print("floor base ok")
    return 0

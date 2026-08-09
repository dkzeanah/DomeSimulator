"""A library of your own designs: triangles, and groups made from them.

This is the compositional model the whole tool is built around, written
down explicitly:

    strut profiles  ->  a triangle  ->  a pentagon or an hourglass  ->  a dome

A **triangle design** is three strut specs plus a fill -- exactly what
the Panel Creator produces. A **pentagon design** is five references to
triangle designs, and an **hourglass design** is two plus the joint at
the waist. Groups store *references*, not copies, so fixing a triangle
fixes every group built from it.

Designs live in the preset file next to the layers, so a saved dome
carries the parts it was made from rather than just the finished result.
"""

from __future__ import annotations

from dataclasses import dataclass, field


def _slot_names(count: int) -> tuple[str, ...]:
    return tuple("ABCDE"[:count])


@dataclass
class TriangleDesign:
    """Three struts and a fill -- one buildable panel."""

    name: str
    struts: tuple[str, str, str] = ("lumber_2x4",) * 3
    fill: str = "polycarbonate"

    @property
    def signature(self) -> tuple:
        """What makes two triangles the same part. Used to avoid saving a
        second copy of a design that already exists under another name."""
        return (tuple(self.struts), self.fill)

    def to_json(self) -> dict:
        return {"name": self.name, "struts": list(self.struts),
                "fill": self.fill}

    @staticmethod
    def from_json(data: dict) -> "TriangleDesign":
        struts = list(data.get("struts", ["lumber_2x4"] * 3))
        while len(struts) < 3:
            struts.append("lumber_2x4")
        return TriangleDesign(str(data.get("name", "Triangle")),
                              tuple(struts[:3]),
                              str(data.get("fill", "polycarbonate")))


@dataclass
class GroupDesign:
    """A pentagon (five triangles) or an hourglass (two, plus a joint),
    stored as references to triangle designs."""

    name: str
    kind: str                       # "pentagon" | "hourglass"
    triangles: tuple[str, ...] = ()
    joint: str = "banding"

    @property
    def slots(self) -> int:
        return 5 if self.kind == "pentagon" else 2

    def to_json(self) -> dict:
        return {"name": self.name, "kind": self.kind,
                "triangles": list(self.triangles), "joint": self.joint}

    @staticmethod
    def from_json(data: dict) -> "GroupDesign":
        return GroupDesign(
            str(data.get("name", "Group")),
            str(data.get("kind", "pentagon")),
            tuple(str(t) for t in data.get("triangles", ())),
            str(data.get("joint", "banding")),
        )


class DesignLibrary:
    """Everything the user has named and kept."""

    def __init__(self) -> None:
        self.triangles: dict[str, TriangleDesign] = {}
        self.groups: dict[str, GroupDesign] = {}

    # -- naming ----------------------------------------------------------

    def unique_name(self, wanted: str, existing: dict) -> str:
        """Never silently overwrite: a repeated name gains a suffix."""
        wanted = (wanted or "Untitled").strip() or "Untitled"
        if wanted not in existing:
            return wanted
        index = 2
        while f"{wanted} {index}" in existing:
            index += 1
        return f"{wanted} {index}"

    # -- triangles -------------------------------------------------------

    def save_triangle(self, name: str, struts, fill: str) -> TriangleDesign:
        design = TriangleDesign(self.unique_name(name, self.triangles),
                                tuple(struts), fill)
        self.triangles[design.name] = design
        return design

    def ensure_triangle(self, struts, fill: str,
                        suggested: str = "Triangle") -> str:
        """The name of a design matching this exact composition, creating
        one only if nothing already matches.

        Saving a pentagon shouldn't spray five near-identical triangle
        designs into the library when its faces are all the same part.
        """
        signature = (tuple(struts), fill)
        for design in self.triangles.values():
            if design.signature == signature:
                return design.name
        return self.save_triangle(suggested, struts, fill).name

    def triangle(self, name: str) -> TriangleDesign | None:
        return self.triangles.get(name)

    def delete_triangle(self, name: str) -> None:
        """Removing a part also removes the groups that referenced it,
        rather than leaving a group pointing at something gone."""
        self.triangles.pop(name, None)
        for key in [k for k, g in self.groups.items() if name in g.triangles]:
            self.groups.pop(key, None)

    # -- groups ----------------------------------------------------------

    def save_group(self, name: str, kind: str, triangle_names,
                   joint: str = "banding") -> GroupDesign:
        design = GroupDesign(self.unique_name(name, self.groups), kind,
                             tuple(triangle_names), joint)
        self.groups[design.name] = design
        return design

    def group(self, name: str) -> GroupDesign | None:
        return self.groups.get(name)

    def groups_of(self, kind: str) -> list[GroupDesign]:
        return [g for g in self.groups.values() if g.kind == kind]

    def resolve(self, design: GroupDesign) -> list[TriangleDesign]:
        """A group's triangle designs, in slot order. Any reference that
        no longer exists falls back to a plain default so a partly broken
        preset still opens."""
        out = []
        for name in design.triangles:
            out.append(self.triangles.get(name)
                       or TriangleDesign(name or "missing"))
        while len(out) < design.slots:
            out.append(TriangleDesign("default"))
        return out[:design.slots]

    # -- persistence -----------------------------------------------------

    def to_json(self) -> dict:
        return {
            "triangles": [t.to_json() for t in self.triangles.values()],
            "groups": [g.to_json() for g in self.groups.values()],
        }

    @staticmethod
    def from_json(data: dict) -> "DesignLibrary":
        library = DesignLibrary()
        for entry in data.get("triangles", []):
            design = TriangleDesign.from_json(entry)
            library.triangles[design.name] = design
        for entry in data.get("groups", []):
            design = GroupDesign.from_json(entry)
            library.groups[design.name] = design
        return library


def starter_library() -> DesignLibrary:
    """A few parts to show what the model is for -- including the
    split-log mix this project was asked about."""
    library = DesignLibrary()
    library.save_triangle("Split-log glazed",
                          ("log_half", "lumber_2x2", "log_quarter"),
                          "polycarbonate")
    library.save_triangle("Split-log solid",
                          ("log_half", "lumber_2x2", "log_quarter"),
                          "wood_planks")
    library.save_triangle("2x4 window", ("lumber_2x4",) * 3, "glass")
    library.save_triangle("2x4 solar", ("lumber_2x4",) * 3, "solar")
    library.save_triangle("2x4 vent", ("lumber_2x4",) * 3, "vent")
    library.save_group("Split-log pentagon", "pentagon",
                       ("Split-log glazed",) * 5)
    library.save_group("Solar pentagon", "pentagon", ("2x4 solar",) * 5)
    library.save_group("Vented pentagon", "pentagon",
                       ("2x4 vent", "2x4 window", "2x4 vent",
                        "2x4 window", "2x4 window"))
    library.save_group("Split-log hourglass", "hourglass",
                       ("Split-log solid",) * 2, "wood_brace")
    return library

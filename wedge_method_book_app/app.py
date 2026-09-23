from __future__ import annotations

import json
import os
import re
import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import inch
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch as rl_inch
    from reportlab.platypus import (
        BaseDocTemplate,
        Frame,
        KeepTogether,
        PageBreak,
        PageTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError:
    colors = None
    TA_CENTER = None
    inch = None
    ParagraphStyle = None
    getSampleStyleSheet = None
    rl_inch = None
    BaseDocTemplate = None
    Frame = None
    KeepTogether = None
    PageBreak = None
    PageTemplate = None
    Paragraph = None
    Spacer = None
    Table = None
    TableStyle = None


APP_TITLE = "The Wedge Method - Book Builder"
PROJECT_EXTENSION = ".wedgebook.json"
LLM_RESPONSE_SCHEMA = "wedgebook.section.v1"
LLM_BEGIN_MARKER = "<<<WEDGEBOOK_SECTION_V1>>>"
LLM_DRAFT_MARKER = "<<<DRAFT_TEXT>>>"
LLM_NOTES_MARKER = "<<<DEVELOPMENT_NOTES_APPEND>>>"
LLM_END_MARKER = "<<<END_WEDGEBOOK_SECTION>>>"


AUTHOR_VOICE_INSTRUCTIONS = r"""
THE WEDGE METHOD - AUTHOR / LLM WRITING INSTRUCTIONS

Purpose
This project is a practical construction and design book about timber geodesic domes, the wedge method, its geometry, fabrication, assembly, enclosure, utility interfaces, and variations. Add useful content to the book without changing the author's voice or turning it into generic AI prose.

Author voice
- Write like a builder, fabricator, programmer, and technical problem-solver explaining a system to another capable person.
- Prefer direct language over academic language.
- Explain what a part does before introducing equations or jargon.
- Use concrete dimensions, examples, diagrams, cut logic, and practical consequences wherever possible.
- Short paragraphs are preferred. Use tables when dimensions or options are easier to compare visually.
- It is acceptable to say "we" when walking the reader through a construction process. Use "I" only when the project notes explicitly document that the author personally built, measured, tested, observed, or decided something.
- Do not write marketing fluff, inspirational filler, canned introductions, fake quotations, or phrases such as "in today's rapidly evolving world," "delve," "game changer," "revolutionary," or "it is important to note."
- Do not repeatedly summarize what was just said. Move the construction logic forward.
- The prose should read like it was written and revised by the book's human author, not like a chatbot transcript.

Technical integrity
- Never invent measurements, test results, load ratings, wind ratings, snow ratings, span capacity, fastener capacity, code compliance, engineering approval, material properties, or personal build history.
- Never claim that an experimental configuration is structurally safe simply because the geometry can be drawn.
- Separate information into these categories when appropriate:
  GEOMETRY - mathematically derived relationships.
  BUILD NOTE - documented fabrication or assembly experience.
  DESIGN VARIATION - a plausible modification of the basic method.
  EXPERIMENTAL - an idea requiring testing, calculation, or engineering validation.
  SAFETY / ENGINEERING - information where loads, code, electrical, plumbing, fire, soil, foundation, occupancy, or professional review matters.
- If source information conflicts, do not silently choose one. Flag the conflict in development notes.
- Show units and preserve unit conversions. For builder-facing dimensions, inches and feet should be readable as fractions or decimals appropriate to the operation.
- Distinguish nominal lumber dimensions from actual dressed dimensions.
- State assumptions used in calculations.
- Whenever a dimension is derived from dome frequency, truncation, radius, diameter, or sphere geometry, identify the geometry being assumed.

Sources and citations
- Do not fabricate citations.
- When a technical claim needs external support, insert a development-note marker in this format:
  [SOURCE NEEDED: concise description of claim]
- Keep quoted material minimal. Prefer paraphrase and cite the original source.
- Building-code requirements must be tied to a specific jurisdiction and code edition if they are stated as requirements.

How to add a new section
1. Read the chapter goal and development notes first.
2. Identify whether the section is geometry, tested construction, design variation, experimental design, or safety/engineering.
3. Draft the practical explanation first.
4. Add equations only where they help the reader calculate or fabricate something.
5. Add a worked example if the section contains a calculation.
6. Add figure recommendations in development notes using:
   [FIGURE: description]
7. Add table recommendations using:
   [TABLE: description]
8. Add missing research needs using:
   [SOURCE NEEDED: description]
9. Never fabricate an author's personal anecdote to make the text sound human.
10. Preserve the author's existing terminology unless a correction is technically necessary; if so, explain the correction in development notes rather than silently rewriting the conceptual system.

Reference build
The manuscript uses a 20-foot-diameter 2V dome as a recurring reference build. Use it to make abstract geometry concrete, but do not assume dimensions that have not been calculated and verified for the exact 2V configuration used by the book.

Book organization
The reader should be able to move through this sequence:
geometry -> wedge fabrication -> strut fabrication -> connections -> base layout -> dome assembly -> openings -> shell/panels -> foundations/floor -> utilities -> environmental control -> variations -> modular systems -> applications -> reference designs -> builder tables.

Editing rule
When revising existing text, preserve useful technical detail. Do not "simplify" by removing dimensions, assumptions, exceptions, warnings, or construction logic. If something is wrong, correct it and record the reason in development notes.
""".strip()


DISCLAIMER_TEXT = (
    "This book documents construction methods, geometric principles, experimental designs, "
    "and prototype concepts. It is not a substitute for site-specific structural engineering. "
    "Building codes, loads, materials, soil conditions, permitting requirements, electrical rules, "
    "plumbing rules, and fire-safety requirements vary by location. Structural designs intended for "
    "permanent occupancy should be reviewed for the applicable site, loads, materials, connections, "
    "foundation, and local requirements by appropriately qualified professionals and authorities."
)


INTRODUCTION_DRAFT = """A geodesic dome looks complicated until you stop looking at the whole dome.

From a distance it looks like a curved structure made from dozens of parts pointing in different directions. Up close, it becomes something much simpler. It is a collection of straight pieces arranged into triangles.

That difference is important.

The dome looks curved, but the individual structural members do not have to be curved. A builder can create a large rounded structure using straight pieces of lumber, repeatable cuts, and a relatively small number of different part dimensions.

Most geodesic dome systems solve the problem of connecting those pieces with some type of hub, plate, bracket, flattened strut end, or specially manufactured connector.

The wedge method approaches the problem differently.

Instead of treating the strut as a rectangular member that must somehow be forced into the geometry of the dome, the shape of the structural member itself becomes part of that geometry.

The member is cut as a wedge.

The narrow portion of the wedge faces toward the inside of the dome and the wider portion faces toward the outside. When the members are arranged into triangles and the triangles begin joining one another, the changing thickness of the members helps create the angular relationship between neighboring faces.

This does not eliminate geometry. It uses geometry.

That distinction is the basis of this book.

The purpose of this book is not to describe one dome with one set of measurements. The goal is to explain a method of building geodesic structures so that the builder understands what the parts are doing, how they can be produced, how the system can be scaled, and how different construction approaches can grow from the same basic idea.

Some versions may begin with ordinary dimensional lumber. Others may begin with larger timbers. A builder with access to logs may choose to divide the log longitudinally and recover multiple wedge-shaped structural members from the same piece of wood.

Other versions could use laminated members, manufactured components, metal reinforcement, removable panels, insulated shells, or entirely different enclosure systems.

The frame and the enclosure also do not necessarily have to be treated as the same thing.

A structural dome can support plywood panels, fiberglass panels, transparent panels, insulated composite panels, or a removable shell. Doors and windows can be introduced by reinforcing openings in the triangular structure. Utilities can enter through the floor, through a dedicated service location, or through a central utility system.

Once the geometry and construction method are understood, the dome stops being one particular building and becomes a platform.

That is where this book is headed.

We will begin with the basic geometry of the dome and the wedge-shaped structural member. From there we will move through material selection, fabrication, repetitive cutting, connections, assembly, foundations, panels, openings, utilities, and several variations of the system.

A reference dome will be used throughout the book so that the geometry does not remain abstract. The same principles will then be scaled and modified to show how the method can be applied to structures of different sizes and purposes.

Some information in this book is mathematical. Some comes from fabrication and construction. Some sections explore design possibilities that may require additional testing or engineering before being used in an occupied structure.

Those categories will be identified rather than treated as if they are the same thing.

A dome intended to hold tools is not necessarily designed to the same requirements as a permanent residence. Snow, wind, soil, foundations, fasteners, fire safety, electrical systems, plumbing systems, and local building requirements can all change what is acceptable for a particular project.

This book therefore focuses on understanding and constructing the system rather than replacing project-specific structural engineering or local code requirements.

The basic idea, however, is simple:

Start with straight material.

Understand the triangle.

Shape the member to participate in the geometry.

Repeat the part accurately.

Connect the triangles.

And allow many simple pieces to become one structure."""


PARTS: List[Tuple[str, List[Tuple[str, List[str]]]]] = [
    (
        "Part I - Understanding the System",
        [
            (
                "1. Why Build a Dome?",
                [
                    "What a geodesic dome is",
                    "Why triangles are used",
                    "Frequency",
                    "Chords versus curved surfaces",
                    "Traditional strut/hub construction",
                    "Panelized domes",
                    "Where the wedge method differs",
                ],
            ),
            (
                "2. The Wedge Method",
                [
                    "Basic concept",
                    "Wedge-shaped structural members",
                    "Wide side / narrow side orientation",
                    "Inward-pointing wedge geometry",
                    "Hubless or reduced-hardware construction",
                    "Using lumber versus logs",
                    "How the wedge influences the final shell geometry",
                ],
            ),
            (
                "3. Understanding Dome Geometry",
                [
                    "Radius and diameter",
                    "Sphere versus dome",
                    "Frequency",
                    "1V, 2V, 3V, and higher frequencies",
                    "Chord lengths",
                    "A/B/C strut families",
                    "Triangle types",
                    "Triangle heights",
                    "Dihedral relationships",
                    "Scaling a design",
                ],
            ),
        ],
    ),
    (
        "Part II - Making the Structure",
        [
            (
                "4. Materials",
                [
                    "Dimensional lumber",
                    "Sawn timber",
                    "Logs",
                    "Species",
                    "Moisture",
                    "Knots and defects",
                    "Grain direction",
                    "Fasteners",
                    "Plates and reinforcement",
                ],
            ),
            (
                "5. Turning Timber Into Wedges",
                [
                    "Layout",
                    "Ripping",
                    "Log division",
                    "Wedge extraction",
                    "Saw setups",
                    "Jigs",
                    "Repetitive cutting",
                    "Tolerances",
                    "Labeling",
                ],
            ),
            (
                "6. Making the Struts",
                [
                    "Cutting length",
                    "End geometry",
                    "Repeatability",
                    "A and B members",
                    "Test fitting",
                    "Error checking",
                    "Mass-production workflow",
                ],
            ),
            (
                "7. Connections",
                [
                    "Direct wood joints",
                    "Screws",
                    "Structural screws",
                    "Bolts",
                    "Washers",
                    "Plates",
                    "Internal brackets",
                    "External brackets",
                    "Temporary assembly joints",
                    "Replaceable connections",
                ],
            ),
        ],
    ),
    (
        "Part III - Building the Dome",
        [
            (
                "8. Laying Out the Base",
                [
                    "Finding center",
                    "Radius layout",
                    "Polygon/base geometry",
                    "Foundation interfaces",
                    "Leveling",
                    "Establishing reference points",
                ],
            ),
            (
                "9. Assembly",
                [
                    "First course",
                    "Triangle assembly",
                    "Raising sections",
                    "Temporary bracing",
                    "Course-by-course construction",
                    "Apex closure",
                    "Alignment correction",
                ],
            ),
            (
                "10. Doors, Windows, and Openings",
                [
                    "Removing structural triangles",
                    "Reinforcing openings",
                    "Door frames",
                    "Window frames",
                    "Entry extensions",
                    "Avoiding weak discontinuities",
                ],
            ),
        ],
    ),
    (
        "Part IV - Turning the Frame Into a Building",
        [
            (
                "11. Panels and Shells",
                [
                    "Plywood",
                    "Composite panels",
                    "Fiberglass",
                    "Metal",
                    "Transparent panels",
                    "Insulated panels",
                    "Removable panels",
                    "Snap-in concepts",
                    "Weather seals",
                ],
            ),
            (
                "12. Floor and Foundation Systems",
                [
                    "Slab",
                    "Ring foundation",
                    "Pier foundation",
                    "Raised deck",
                    "Portable platform",
                    "Prepared building pad",
                ],
            ),
            (
                "13. Utilities",
                [
                    "Electrical entry",
                    "Water entry",
                    "Plumbing",
                    "Central utility column",
                    "Utility routing through the floor",
                    "Apex routing",
                    "Exterior routing",
                    "Gasketed interface penetrations",
                    "Replaceable service connections",
                ],
            ),
            (
                "14. Environmental Control",
                [
                    "Insulation",
                    "Condensation",
                    "Ventilation",
                    "Heating",
                    "Cooling",
                    "Solar gain",
                    "Shading",
                    "Moisture management",
                ],
            ),
        ],
    ),
    (
        "Part V - Variations and Future Systems",
        [
            (
                "15. Variations of the Wedge Method",
                [
                    "Solid wedges",
                    "Hollow members",
                    "Laminated wedges",
                    "Split wedges",
                    "Log-derived wedges",
                    "Manufactured wedges",
                    "Hybrid metal/wood systems",
                ],
            ),
            (
                "16. Different Dome Configurations",
                [
                    "1V",
                    "2V",
                    "3V",
                    "Hemispheres",
                    "Partial spheres",
                    "Knee-wall domes",
                    "Raised domes",
                ],
            ),
            (
                "17. Modular Dome Construction",
                [
                    "Prefabricated triangles",
                    "Panel modules",
                    "Replaceable exterior shells",
                    "Transportable components",
                    "Kit construction",
                    "Standardized interfaces",
                ],
            ),
            (
                "18. The Dome as a Platform",
                [
                    "Workshops",
                    "Cabins",
                    "Greenhouses",
                    "Temporary housing",
                    "Semi-mobile structures",
                    "Prepared dome pads",
                    "Multi-dome compounds",
                    "Connected structures",
                ],
            ),
            (
                "19. Reference Designs",
                [
                    "Small demonstration dome",
                    "12-foot dome",
                    "16-foot dome",
                    "20-foot reference dome",
                    "Larger examples",
                ],
            ),
            (
                "20. Builder's Reference",
                [
                    "Strut tables",
                    "Triangle tables",
                    "Surface area",
                    "Floor area",
                    "Member count",
                    "Material quantities",
                    "Conversion tables",
                    "Cut worksheets",
                    "Blank project sheets",
                ],
            ),
        ],
    ),
]


ILLUSTRATION_CHECKLIST = [
    "Complete 2V dome",
    "Exploded 2V dome",
    "A-member highlighting",
    "B-member highlighting",
    "Two triangle families",
    "Wedge cross-section",
    "Conventional rectangular strut versus wedge strut",
    "Log divided into wedge members",
    "Dimensional-lumber wedge-cutting layouts",
    "Inward wedge orientation",
    "Three-member vertex",
    "Five-member vertex",
    "Six-member vertex where applicable",
    "Dihedral relationship",
    "Triangle-to-triangle joint",
    "Base attachment",
    "First course",
    "Second course",
    "Apex assembly",
    "Door opening",
    "Reinforced opening",
    "Removable panel",
    "Insulated panel",
    "Utility column",
    "Floor utility interface",
    "Apex utility interface",
    "Gasketed service cap",
    "Prepared dome pad",
    "Completed dome cutaway",
]


# Structured figure planning is kept separately from the editable build-out text so an
# older project file can never lose the original breadth of the illustration program.
# Every illustration from the first book plan above appears in at least one chapter plan.
CHAPTER_ILLUSTRATION_PLAN: Dict[int, List[str]] = {
    1: [
        "Complete 2V dome",
        "Conventional rectangular strut versus wedge strut",
        "Simple triangle-to-curved-shell explanation diagram",
    ],
    2: [
        "Wedge cross-section",
        "Conventional rectangular strut versus wedge strut",
        "Inward wedge orientation",
        "Three-member vertex",
        "Five-member vertex",
        "Six-member vertex where applicable",
    ],
    3: [
        "Exploded 2V dome",
        "A-member highlighting",
        "B-member highlighting",
        "Two triangle families",
        "Dihedral relationship",
    ],
    4: [
        "Nominal versus actual lumber cross-section",
        "Grain/defect examples for member selection",
    ],
    5: [
        "Log divided into wedge members",
        "Dimensional-lumber wedge-cutting layouts",
        "Saw/jig sequence for repetitive wedge production",
    ],
    6: [
        "A-member highlighting",
        "B-member highlighting",
        "Strut end-geometry and checking-jig detail",
    ],
    7: [
        "Three-member vertex",
        "Five-member vertex",
        "Six-member vertex where applicable",
        "Triangle-to-triangle joint",
        "Exploded fastener/plate alternatives",
    ],
    8: [
        "Base attachment",
        "Prepared dome pad",
        "Center/radius/base-polygon layout diagram",
    ],
    9: [
        "First course",
        "Second course",
        "Apex assembly",
        "Temporary bracing and raising sequence",
    ],
    10: [
        "Door opening",
        "Reinforced opening",
        "Window-frame integration diagram",
    ],
    11: [
        "Removable panel",
        "Insulated panel",
        "Panel-to-wedge weather-seal detail",
    ],
    12: [
        "Base attachment",
        "Prepared dome pad",
        "Slab/ring/pier/raised-floor comparison sections",
    ],
    13: [
        "Utility column",
        "Floor utility interface",
        "Apex utility interface",
        "Gasketed service cap",
    ],
    14: [
        "Completed dome cutaway",
        "Insulation/ventilation/condensation path section",
    ],
    15: [
        "Wedge cross-section",
        "Solid, hollow, laminated, split, log-derived, and hybrid wedge comparison",
    ],
    16: [
        "Complete 2V dome",
        "Exploded 2V dome",
        "Frequency and truncation comparison silhouettes",
    ],
    17: [
        "Removable panel",
        "Prefabricated triangle module",
        "Standardized interface / transportable module concept",
    ],
    18: [
        "Utility column",
        "Prepared dome pad",
        "Completed dome cutaway",
        "Multi-dome / connected-dome concept plan",
    ],
    19: [
        "Reference-design comparison sheet: demonstration, 12-ft, 16-ft, 20-ft, larger",
        "Complete 2V dome",
    ],
    20: [
        "Builder reference table legend",
        "Cut-list worksheet example",
        "Material-yield worksheet example",
    ],
}


PRODUCTION_ELEMENTS = """BOOK BUILD-OUT ELEMENTS

Core format
- Working title: The Wedge Method
- Subtitle: A Builder's Guide to Timber Geodesic Domes
- Subject: geometry, fabrication, assembly, enclosure, utilities, and variations of the timber wedge method
- Primary print target: 8.5 x 11 inch paperback manual
- Reference build: 20-foot-diameter 2V dome
- Draft target length: approximately 180-300 illustrated pages

Information classes used throughout the manuscript
GEOMETRY - mathematically derived information.
BUILD NOTE - information supported by documented fabrication or assembly experience.
DESIGN VARIATION - a modification that can be derived from the basic system.
EXPERIMENTAL - a possibility requiring testing, calculation, or engineering validation.
SAFETY / ENGINEERING - information where loads, code, electrical, plumbing, fire, soil, foundation, occupancy, or professional review matters.

Recurring reference-build box
Use a clearly marked "REFERENCE BUILD - 20 FT 2V DOME" box whenever a chapter can show how an abstract concept applies to the reference structure. Exact dimensions must be calculated and verified before publication.

Illustration program
""" + "\n".join(f"- {item}" for item in ILLUSTRATION_CHECKLIST) + """

Tables and worksheets to develop
- Verified 2V chord-factor table for the exact dome truncation used in the book
- Diameter-to-strut-length tables
- Triangle side and altitude tables
- Vertex/member-count tables
- Wedge cross-section and taper tables
- Cut-list worksheet
- Material-yield worksheet for logs and dimensional lumber
- Fastener schedule worksheet (project-specific; not universal engineering values)
- Panel dimensions and surface-area worksheets
- Floor-area and circumference tables
- Unit-conversion table
- Blank builder project sheet

Research / verification queue
- Verify all dome geometry against a reproducible mathematical source or derivation
- Define the exact 2V sphere subdivision and truncation used by the reference build
- Document the wedge angle and the relationship between wedge taper and face-to-face dome geometry
- Test and photograph representative joints
- Record real saw setups, jigs, cut sequence, tolerances, and measured error
- Record material species, nominal/actual dimensions, and moisture condition for physical examples
- Photograph or render assembly stages
- Separate concept renderings from tested builds
- Obtain reliable sources for structural-geometry background and material properties where used
- Treat building-code statements by jurisdiction and code edition rather than as universal rules
- Have structural claims intended for occupied buildings professionally reviewed before presenting them as construction specifications

Writing workflow
1. Develop geometry and terminology first.
2. Freeze the reference-dome definition.
3. Build verified strut/triangle tables.
4. Document the actual wedge-fabrication process.
5. Document joint alternatives and which ones were physically tested.
6. Write assembly chapters from actual build order.
7. Add shell, foundation, utility, and environmental-control systems.
8. Add design variations only after the baseline system is clear.
9. Add reference designs and builder worksheets last.
10. Perform a final contradiction pass across all tables, dimensions, figure labels, and terminology before KDP export.

LLM handoff / upload workflow
- Use Write Next Section to locate the first unwritten canonical section and copy a complete brief.
- The brief carries the exact project path, section title, chapter goal, section development notes, neighboring sections, relevant illustration needs, reference-build context, and author rules.
- The LLM must return a WEDGEBOOK_SECTION_V1 envelope so the response can be inserted without manually deciding where it belongs.
- Paste that response into the LLM Upload tab or load a .txt/.md response file, then use Insert Response Into Book.
- The importer verifies the target path and title before changing the manuscript.
- Returned research, figure, and verification needs belong in Development Notes rather than being invented into manuscript prose.
""".strip()


def section_note(chapter_title: str, section_title: str) -> str:
    lower = section_title.lower()
    lines = [
        f"SECTION GOAL: Explain '{section_title}' as it applies to {chapter_title}.",
        "",
        "Development requirements:",
        "- Start with the practical purpose before theory.",
        "- Identify whether the material is geometry, build note, design variation, experimental, or safety/engineering.",
        "- Add exact dimensions only when verified for the stated configuration.",
        "- Recommend a figure when the idea is spatial or difficult to understand from prose alone.",
    ]

    geometry_terms = ("radius", "diameter", "sphere", "frequency", "chord", "strut", "triangle", "dihedral", "scaling", "1v", "2v", "3v", "surface area", "floor area", "member count")
    safety_terms = ("foundation", "fastener", "bolt", "screw", "electrical", "water", "plumbing", "opening", "door", "window", "insulation", "heating", "cooling", "moisture", "fire")
    fabrication_terms = ("ripping", "layout", "jig", "cut", "label", "tolerance", "log", "lumber", "wedge", "assembly", "bracing", "apex")

    if any(term in lower for term in geometry_terms):
        lines += [
            "- Include the governing relationship or formula if it can be stated accurately.",
            "- Include a worked reference-build example after the formula is verified.",
            "- Record assumptions about sphere subdivision, truncation, and units.",
        ]
    if any(term in lower for term in safety_terms):
        lines += [
            "- Do not present a universal load or code claim without project-specific support.",
            "- Identify where local code, engineering, manufacturer data, or jurisdiction-specific requirements control the design.",
        ]
    if any(term in lower for term in fabrication_terms):
        lines += [
            "- Record the actual tool setup, workholding, cut order, repeatability method, and measured tolerance when available.",
            "- Describe failure modes and common fabrication errors where they are known from documented work.",
        ]

    lines += [
        "",
        "Suggested development markers:",
        f"[FIGURE: {section_title} illustrated for the wedge-method system]",
        f"[SOURCE NEEDED: any external technical claim used in {section_title}]",
    ]
    return "\n".join(lines)


def make_default_project() -> Dict[str, Any]:
    project: Dict[str, Any] = {
        "schema_version": 2,
        "metadata": {
            "title": "The Wedge Method",
            "subtitle": "A Builder's Guide to Timber Geodesic Domes",
            "author": "Donovan Zeanah",
            "reference_build": "20-foot-diameter 2V dome",
            "print_size": "8.5x11",
        },
        "front_matter": {
            "disclaimer": DISCLAIMER_TEXT,
            "introduction": INTRODUCTION_DRAFT,
        },
        "parts": [],
        "author_voice_instructions": AUTHOR_VOICE_INSTRUCTIONS,
        "production_elements": PRODUCTION_ELEMENTS,
        "illustration_checklist": list(ILLUSTRATION_CHECKLIST),
        "chapter_illustration_plan": deepcopy(CHAPTER_ILLUSTRATION_PLAN),
        "reference_sources": [],
    }

    for part_title, chapters in PARTS:
        part = {"title": part_title, "body": "", "notes": "", "chapters": []}
        for chapter_title, section_titles in chapters:
            chapter = {
                "title": chapter_title,
                "body": "",
                "notes": (
                    f"CHAPTER GOAL: Build a practical, illustrated chapter covering {chapter_title}.\n\n"
                    "Use the 20-foot 2V reference dome when a verified worked example helps. "
                    "Keep tested construction, derived geometry, and untested possibilities visibly separate."
                ),
                "sections": [],
            }
            for s in section_titles:
                chapter["sections"].append({"title": s, "body": "", "notes": section_note(chapter_title, s)})
            part["chapters"].append(chapter)
        project["parts"].append(part)

    return project


def ensure_canonical_outline(project: Dict[str, Any]) -> bool:
    """Add any canonical parts/chapters/sections missing from an older project without deleting user work."""
    changed = False
    project.setdefault("parts", [])

    for p_idx, (part_title, canonical_chapters) in enumerate(PARTS):
        if p_idx >= len(project["parts"]):
            project["parts"].append({"title": part_title, "body": "", "notes": "", "chapters": []})
            changed = True
        part = project["parts"][p_idx]
        part.setdefault("title", part_title)
        part.setdefault("body", "")
        part.setdefault("notes", "")
        part.setdefault("chapters", [])

        for c_idx, (chapter_title, canonical_sections) in enumerate(canonical_chapters):
            if c_idx >= len(part["chapters"]):
                part["chapters"].append({
                    "title": chapter_title,
                    "body": "",
                    "notes": (
                        f"CHAPTER GOAL: Build a practical, illustrated chapter covering {chapter_title}.\n\n"
                        "Use the 20-foot 2V reference dome when a verified worked example helps. "
                        "Keep tested construction, derived geometry, and untested possibilities visibly separate."
                    ),
                    "sections": [],
                })
                changed = True
            chapter = part["chapters"][c_idx]
            chapter.setdefault("title", chapter_title)
            chapter.setdefault("body", "")
            chapter.setdefault("notes", "")
            chapter.setdefault("sections", [])

            existing_titles = {sec.get("title", "").strip().casefold() for sec in chapter["sections"]}
            for section_title in canonical_sections:
                if section_title.strip().casefold() not in existing_titles:
                    chapter["sections"].append({
                        "title": section_title,
                        "body": "",
                        "notes": section_note(chapter.get("title", chapter_title), section_title),
                    })
                    existing_titles.add(section_title.strip().casefold())
                    changed = True

    project.setdefault("front_matter", {})
    project["front_matter"].setdefault("disclaimer", DISCLAIMER_TEXT)
    project["front_matter"].setdefault("introduction", INTRODUCTION_DRAFT)
    project.setdefault("author_voice_instructions", AUTHOR_VOICE_INSTRUCTIONS)
    project.setdefault("production_elements", PRODUCTION_ELEMENTS)
    project.setdefault("reference_sources", [])
    project.setdefault("illustration_checklist", list(ILLUSTRATION_CHECKLIST))
    project.setdefault("chapter_illustration_plan", deepcopy(CHAPTER_ILLUSTRATION_PLAN))
    if int(project.get("schema_version", 0) or 0) < 2:
        project["schema_version"] = 2
        changed = True
    return changed


def parse_llm_section_response(text: str) -> Dict[str, Any]:
    """Parse the plain-text interchange envelope returned by an LLM."""
    start = text.find(LLM_BEGIN_MARKER)
    end = text.find(LLM_END_MARKER)
    if start < 0 or end < 0 or end <= start:
        raise ValueError(
            "The response does not contain a complete WEDGEBOOK_SECTION_V1 envelope. "
            "Copy the entire LLM response, including its begin/end markers."
        )

    payload = text[start + len(LLM_BEGIN_MARKER):end].strip()
    draft_pos = payload.find(LLM_DRAFT_MARKER)
    notes_pos = payload.find(LLM_NOTES_MARKER)
    if draft_pos < 0 or notes_pos < 0 or notes_pos <= draft_pos:
        raise ValueError("The response envelope is missing the Draft Text or Development Notes marker.")

    header = payload[:draft_pos].strip()
    draft = payload[draft_pos + len(LLM_DRAFT_MARKER):notes_pos].strip()
    notes = payload[notes_pos + len(LLM_NOTES_MARKER):].strip()

    values: Dict[str, str] = {}
    for line in header.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip().upper()] = value.strip()

    if values.get("SCHEMA") != LLM_RESPONSE_SCHEMA:
        raise ValueError(f"Unsupported or missing response schema. Expected {LLM_RESPONSE_SCHEMA}.")

    path_text = values.get("TARGET_PATH", "")
    match = re.fullmatch(r"(\d+)/(\d+)/(\d+)", path_text)
    if not match:
        raise ValueError("TARGET_PATH must use zero-based part/chapter/section indexes like 0/1/3.")

    if not draft:
        raise ValueError("The LLM response contains no manuscript text in the Draft Text section.")

    return {
        "schema": values.get("SCHEMA", ""),
        "target_path": tuple(int(x) for x in match.groups()),
        "target_title": values.get("TARGET_TITLE", ""),
        "chapter_title": values.get("CHAPTER_TITLE", ""),
        "draft_text": draft,
        "development_notes_append": notes,
    }




def normalize_for_reportlab(text: str) -> str:
    """Convert common Unicode punctuation to characters supported by built-in PDF fonts."""
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2026": "...",
        "\u00a0": " ",
        "\u00d7": "x",
        "\u2260": "!=",
        "\u2192": "->",
        "\u00b0": " degrees",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("cp1252", errors="replace").decode("cp1252")


def html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def text_to_paragraphs(text: str) -> List[str]:
    """Split editor text into paragraph-sized chunks while preserving simple bullet lines."""
    blocks: List[str] = []
    current: List[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            if current:
                blocks.append("\n".join(current))
                current = []
            continue
        if line.lstrip().startswith(("- ", "* ")):
            if current:
                blocks.append("\n".join(current))
                current = []
            blocks.append(line)
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks


class NumberedCanvasMixin:
    pass


class BookBuilderApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1500x900")
        self.minsize(1100, 700)

        self.project: Dict[str, Any] = make_default_project()
        ensure_canonical_outline(self.project)
        self.project_path: Optional[Path] = None
        self.current_node: Optional[Tuple[str, ...]] = None
        self.last_llm_target: Optional[Tuple[int, int, int]] = None
        self.dirty = False

        self.pdf_doc = None
        self.pdf_path: Optional[Path] = None
        self.pdf_page_index = 0
        self.pdf_zoom = 1.2
        self.pdf_photo = None

        self._configure_styles()
        self._build_menu()
        self._build_ui()
        self._populate_tree()
        self._load_static_panels()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=24)
        style.configure("TNotebook.Tab", padding=(10, 5))

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="New Project", command=self.new_project, accelerator="Ctrl+N")
        file_menu.add_command(label="Open Project...", command=self.open_project, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Project", command=self.save_project, accelerator="Ctrl+S")
        file_menu.add_command(label="Save Project As...", command=self.save_project_as)
        file_menu.add_separator()
        file_menu.add_command(label="Open Reference PDF...", command=self.open_reference_pdf, accelerator="Ctrl+R")
        file_menu.add_separator()
        file_menu.add_command(label="Export Manuscript PDF...", command=lambda: self.export_pdf(False))
        file_menu.add_command(label="Export Development Outline PDF...", command=lambda: self.export_pdf(True))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=False)
        edit_menu.add_command(label="Add Section Below", command=self.add_section)
        edit_menu.add_command(label="Rename Selected", command=self.rename_selected)
        edit_menu.add_command(label="Delete Selected Section", command=self.delete_selected)
        edit_menu.add_separator()
        edit_menu.add_command(label="Find in Current Editor...", command=self.find_in_editor, accelerator="Ctrl+F")
        menubar.add_cascade(label="Edit", menu=edit_menu)

        ai_menu = tk.Menu(menubar, tearoff=False)
        ai_menu.add_command(label="Write Next Available Section (Copy Brief)", command=self.copy_next_section_brief)
        ai_menu.add_command(label="Upload / Insert LLM Response...", command=self.show_llm_upload)
        ai_menu.add_separator()
        ai_menu.add_command(label="Copy Selected Section Brief", command=self.copy_selected_brief)
        ai_menu.add_command(label="Copy Author / LLM Instructions", command=self.copy_ai_instructions)
        menubar.add_cascade(label="AI / LLM", menu=ai_menu)

        self.config(menu=menubar)
        self.bind_all("<Control-n>", lambda _e: self.new_project())
        self.bind_all("<Control-o>", lambda _e: self.open_project())
        self.bind_all("<Control-s>", lambda _e: self.save_project())
        self.bind_all("<Control-r>", lambda _e: self.open_reference_pdf())
        self.bind_all("<Control-f>", lambda _e: self.find_in_editor())

    def _build_ui(self) -> None:
        toolbar = ttk.Frame(self, padding=6)
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="Open Project", command=self.open_project).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Save", command=self.save_project).pack(side="left", padx=2)
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(toolbar, text="Reference PDF", command=self.open_reference_pdf).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Export Manuscript", command=lambda: self.export_pdf(False)).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Export Outline", command=lambda: self.export_pdf(True)).pack(side="left", padx=2)
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(toolbar, text="Write Next Section", command=self.copy_next_section_brief).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Upload LLM Response", command=self.show_llm_upload).pack(side="left", padx=2)

        main = ttk.Panedwindow(self, orient="horizontal")
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main, padding=(6, 6, 3, 6))
        center = ttk.Frame(main, padding=(3, 6, 3, 6))
        right = ttk.Frame(main, padding=(3, 6, 6, 6))
        main.add(left, weight=2)
        main.add(center, weight=5)
        main.add(right, weight=4)

        ttk.Label(left, text="Book Outline", font=("TkDefaultFont", 11, "bold")).pack(anchor="w")
        self.tree = ttk.Treeview(left, show="tree", selectmode="browse")
        tree_scroll = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True, pady=(6, 0))
        tree_scroll.pack(side="right", fill="y", pady=(6, 0))
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        editor_header = ttk.Frame(center)
        editor_header.pack(fill="x")
        ttk.Label(editor_header, text="Selected Item", font=("TkDefaultFont", 11, "bold")).pack(side="left")
        self.selected_label = ttk.Label(editor_header, text="")
        self.selected_label.pack(side="left", padx=10)

        self.editor_tabs = ttk.Notebook(center)
        self.editor_tabs.pack(fill="both", expand=True, pady=(6, 0))

        draft_frame = ttk.Frame(self.editor_tabs)
        notes_frame = ttk.Frame(self.editor_tabs)
        self.editor_tabs.add(draft_frame, text="Draft Text")
        self.editor_tabs.add(notes_frame, text="Development Notes")

        self.draft_text = ScrolledText(draft_frame, wrap="word", undo=True, font=("Segoe UI", 11))
        self.draft_text.pack(fill="both", expand=True)
        self.notes_text = ScrolledText(notes_frame, wrap="word", undo=True, font=("Consolas", 10))
        self.notes_text.pack(fill="both", expand=True)

        self.draft_text.bind("<<Modified>>", self._on_editor_modified)
        self.notes_text.bind("<<Modified>>", self._on_editor_modified)
        self.draft_text.bind("<FocusOut>", lambda _e: self.commit_editor())
        self.notes_text.bind("<FocusOut>", lambda _e: self.commit_editor())

        self.right_tabs = ttk.Notebook(right)
        self.right_tabs.pack(fill="both", expand=True)

        ai_frame = ttk.Frame(self.right_tabs)
        upload_frame = ttk.Frame(self.right_tabs)
        build_frame = ttk.Frame(self.right_tabs)
        pdf_frame = ttk.Frame(self.right_tabs)
        self.right_tabs.add(ai_frame, text="Author / LLM Rules")
        self.right_tabs.add(upload_frame, text="LLM Upload")
        self.right_tabs.add(build_frame, text="Build-Out")
        self.right_tabs.add(pdf_frame, text="PDF Reader")

        self.ai_text = ScrolledText(ai_frame, wrap="word", font=("Consolas", 9))
        self.ai_text.pack(fill="both", expand=True)
        ai_buttons = ttk.Frame(ai_frame)
        ai_buttons.pack(fill="x", pady=(4, 0))
        ttk.Button(ai_buttons, text="Write Next Section", command=self.copy_next_section_brief).pack(side="left")
        ttk.Button(ai_buttons, text="Copy Selected Brief", command=self.copy_selected_brief).pack(side="left", padx=6)
        ttk.Button(ai_buttons, text="Copy Full Instructions", command=self.copy_ai_instructions).pack(side="left", padx=6)

        upload_header = ttk.Frame(upload_frame)
        upload_header.pack(fill="x", pady=(0, 4))
        self.upload_target_var = tk.StringVar(value="No LLM response loaded.")
        ttk.Label(upload_header, textvariable=self.upload_target_var, font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        ttk.Label(
            upload_frame,
            text=(
                "Paste the full response returned from a Write Next Section brief, or load a .txt/.md file. "
                "The app reads the embedded target path, verifies the section title, inserts manuscript text, "
                "and appends unresolved figure/source/research items to Development Notes."
            ),
            wraplength=420,
            justify="left",
        ).pack(fill="x", pady=(0, 5))
        self.upload_text = ScrolledText(upload_frame, wrap="word", font=("Consolas", 9))
        self.upload_text.pack(fill="both", expand=True)
        upload_buttons = ttk.Frame(upload_frame)
        upload_buttons.pack(fill="x", pady=(5, 0))
        ttk.Button(upload_buttons, text="Paste Clipboard", command=self.paste_llm_response).pack(side="left")
        ttk.Button(upload_buttons, text="Load Response File", command=self.load_llm_response_file).pack(side="left", padx=5)
        ttk.Button(upload_buttons, text="Insert Response Into Book", command=self.insert_llm_response).pack(side="left", padx=5)
        ttk.Button(upload_buttons, text="Clear", command=self.clear_llm_upload).pack(side="right")

        self.build_text = ScrolledText(build_frame, wrap="word", font=("Consolas", 9))
        self.build_text.pack(fill="both", expand=True)

        pdf_controls = ttk.Frame(pdf_frame)
        pdf_controls.pack(fill="x")
        ttk.Button(pdf_controls, text="Open PDF", command=self.open_reference_pdf).pack(side="left", padx=2)
        ttk.Button(pdf_controls, text="< Prev", command=self.pdf_prev).pack(side="left", padx=2)
        ttk.Button(pdf_controls, text="Next >", command=self.pdf_next).pack(side="left", padx=2)
        self.page_label = ttk.Label(pdf_controls, text="No PDF loaded")
        self.page_label.pack(side="left", padx=8)
        ttk.Button(pdf_controls, text="-", width=3, command=self.pdf_zoom_out).pack(side="right", padx=2)
        ttk.Button(pdf_controls, text="+", width=3, command=self.pdf_zoom_in).pack(side="right", padx=2)

        extract_controls = ttk.Frame(pdf_frame)
        extract_controls.pack(fill="x", pady=(4, 4))
        ttk.Button(extract_controls, text="Append Page Text to Notes", command=self.append_pdf_page_text).pack(side="left")
        ttk.Button(extract_controls, text="Add PDF to Source List", command=self.add_pdf_to_source_list).pack(side="left", padx=6)

        self.pdf_canvas = tk.Canvas(pdf_frame, background="#303030", highlightthickness=0)
        pdf_v = ttk.Scrollbar(pdf_frame, orient="vertical", command=self.pdf_canvas.yview)
        pdf_h = ttk.Scrollbar(pdf_frame, orient="horizontal", command=self.pdf_canvas.xview)
        self.pdf_canvas.configure(yscrollcommand=pdf_v.set, xscrollcommand=pdf_h.set)
        self.pdf_canvas.pack(side="left", fill="both", expand=True)
        pdf_v.pack(side="right", fill="y")
        pdf_h.pack(side="bottom", fill="x")

        self.status_var = tk.StringVar(value="Ready")
        status = ttk.Label(self, textvariable=self.status_var, anchor="w", relief="sunken")
        status.pack(fill="x", side="bottom")

    def _load_static_panels(self) -> None:
        self.ai_text.delete("1.0", "end")
        self.ai_text.insert("1.0", self.project.get("author_voice_instructions", AUTHOR_VOICE_INSTRUCTIONS))
        self.ai_text.configure(state="normal")

        self.build_text.delete("1.0", "end")
        self.build_text.insert("1.0", self.project.get("production_elements", PRODUCTION_ELEMENTS))
        self.build_text.configure(state="normal")

    def _populate_tree(self) -> None:
        self.tree.delete(*self.tree.get_children())

        intro_id = self.tree.insert("", "end", iid="front:introduction", text="Introduction", open=False)
        self.tree.insert("", "end", iid="front:disclaimer", text="Safety / Engineering Disclaimer")

        for p_idx, part in enumerate(self.project["parts"]):
            p_id = f"part:{p_idx}"
            self.tree.insert("", "end", iid=p_id, text=part["title"], open=True)
            for c_idx, chapter in enumerate(part["chapters"]):
                c_id = f"chapter:{p_idx}:{c_idx}"
                self.tree.insert(p_id, "end", iid=c_id, text=chapter["title"], open=False)
                for s_idx, section in enumerate(chapter["sections"]):
                    s_id = f"section:{p_idx}:{c_idx}:{s_idx}"
                    self.tree.insert(c_id, "end", iid=s_id, text=section["title"])

        self.tree.selection_set(intro_id)
        self.tree.focus(intro_id)
        self._load_node(("front", "introduction"))

    def _parse_iid(self, iid: str) -> Tuple[str, ...]:
        return tuple(iid.split(":"))

    def _get_node_data(self, node: Tuple[str, ...]) -> Tuple[str, Dict[str, Any], str, str]:
        kind = node[0]
        if kind == "front":
            key = node[1]
            title = "Introduction" if key == "introduction" else "Safety / Engineering Disclaimer"
            return title, self.project["front_matter"], key, ""
        if kind == "part":
            p = self.project["parts"][int(node[1])]
            return p["title"], p, "body", "notes"
        if kind == "chapter":
            p = self.project["parts"][int(node[1])]
            c = p["chapters"][int(node[2])]
            return c["title"], c, "body", "notes"
        if kind == "section":
            p = self.project["parts"][int(node[1])]
            c = p["chapters"][int(node[2])]
            s = c["sections"][int(node[3])]
            return s["title"], s, "body", "notes"
        raise ValueError(f"Unknown node type: {kind}")

    def on_tree_select(self, _event=None) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        self.commit_editor()
        node = self._parse_iid(selected[0])
        self._load_node(node)

    def _load_node(self, node: Tuple[str, ...]) -> None:
        self.current_node = node
        title, obj, body_key, notes_key = self._get_node_data(node)
        self.selected_label.configure(text=title)

        self.draft_text.delete("1.0", "end")
        self.notes_text.delete("1.0", "end")
        self.draft_text.insert("1.0", obj.get(body_key, ""))
        self.notes_text.insert("1.0", obj.get(notes_key, "") if notes_key else "")
        if not notes_key:
            self.notes_text.insert("1.0", "Front matter item. Development notes are not stored separately for this item.")
        self.draft_text.edit_modified(False)
        self.notes_text.edit_modified(False)
        self.status_var.set(f"Editing: {title}")

    def _on_editor_modified(self, event) -> None:
        widget = event.widget
        if widget.edit_modified():
            self.dirty = True
            widget.edit_modified(False)
            self._update_title()

    def commit_editor(self) -> None:
        if not self.current_node:
            return
        title, obj, body_key, notes_key = self._get_node_data(self.current_node)
        body = self.draft_text.get("1.0", "end-1c")
        notes = self.notes_text.get("1.0", "end-1c")
        if obj.get(body_key, "") != body:
            obj[body_key] = body
            self.dirty = True
        if notes_key and obj.get(notes_key, "") != notes:
            obj[notes_key] = notes
            self.dirty = True
        self._update_title()

    def _update_title(self) -> None:
        name = self.project_path.name if self.project_path else "Untitled Project"
        marker = " *" if self.dirty else ""
        self.title(f"{APP_TITLE} - {name}{marker}")

    def maybe_save(self) -> bool:
        self.commit_editor()
        if not self.dirty:
            return True
        answer = messagebox.askyesnocancel("Unsaved changes", "Save changes before continuing?")
        if answer is None:
            return False
        if answer:
            return self.save_project()
        return True

    def new_project(self) -> None:
        if not self.maybe_save():
            return
        self.project = make_default_project()
        ensure_canonical_outline(self.project)
        self.project_path = None
        self.dirty = False
        self._populate_tree()
        self._load_static_panels()
        self._update_title()

    def open_project(self) -> None:
        if not self.maybe_save():
            return
        path = filedialog.askopenfilename(
            title="Open Wedge Method Book Project",
            filetypes=[("Wedge Book Project", f"*{PROJECT_EXTENSION}"), ("JSON", "*.json"), ("All Files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "parts" not in data or "metadata" not in data:
                raise ValueError("This JSON file is not a valid book project.")
            self.project = data
            upgraded = ensure_canonical_outline(self.project)
            self.project_path = Path(path)
            self.dirty = upgraded
            self._populate_tree()
            self._load_static_panels()
            self._update_title()
            self.status_var.set(f"Opened {self.project_path}")
        except Exception as exc:
            messagebox.showerror("Open failed", str(exc))

    def save_project(self) -> bool:
        self.commit_editor()
        if not self.project_path:
            return self.save_project_as()
        try:
            self._sync_static_panels()
            with open(self.project_path, "w", encoding="utf-8") as f:
                json.dump(self.project, f, indent=2, ensure_ascii=False)
            self.dirty = False
            self._update_title()
            self.status_var.set(f"Saved {self.project_path}")
            return True
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))
            return False

    def save_project_as(self) -> bool:
        self.commit_editor()
        path = filedialog.asksaveasfilename(
            title="Save Wedge Method Book Project",
            defaultextension=PROJECT_EXTENSION,
            initialfile="the_wedge_method.wedgebook.json",
            filetypes=[("Wedge Book Project", f"*{PROJECT_EXTENSION}"), ("JSON", "*.json")],
        )
        if not path:
            return False
        self.project_path = Path(path)
        return self.save_project()

    def _sync_static_panels(self) -> None:
        self.project["author_voice_instructions"] = self.ai_text.get("1.0", "end-1c")
        self.project["production_elements"] = self.build_text.get("1.0", "end-1c")

    def add_section(self) -> None:
        self.commit_editor()
        if not self.current_node:
            return
        node = self.current_node
        if node[0] == "chapter":
            p_idx, c_idx = int(node[1]), int(node[2])
        elif node[0] == "section":
            p_idx, c_idx = int(node[1]), int(node[2])
        else:
            messagebox.showinfo("Add section", "Select a chapter or an existing section first.")
            return
        name = simpledialog.askstring("Add Section", "Section title:")
        if not name:
            return
        chapter = self.project["parts"][p_idx]["chapters"][c_idx]
        chapter["sections"].append({"title": name.strip(), "body": "", "notes": section_note(chapter["title"], name.strip())})
        self.dirty = True
        self._populate_tree()
        new_idx = len(chapter["sections"]) - 1
        iid = f"section:{p_idx}:{c_idx}:{new_idx}"
        self.tree.selection_set(iid)
        self.tree.focus(iid)
        self._load_node(("section", str(p_idx), str(c_idx), str(new_idx)))

    def rename_selected(self) -> None:
        self.commit_editor()
        if not self.current_node or self.current_node[0] == "front":
            messagebox.showinfo("Rename", "Select a part, chapter, or section.")
            return
        title, obj, _body_key, _notes_key = self._get_node_data(self.current_node)
        new = simpledialog.askstring("Rename", "New title:", initialvalue=title)
        if not new:
            return
        obj["title"] = new.strip()
        self.dirty = True
        self._populate_tree()
        self._update_title()

    def delete_selected(self) -> None:
        self.commit_editor()
        if not self.current_node or self.current_node[0] != "section":
            messagebox.showinfo("Delete", "Only user-added or existing sections can be deleted from the GUI.")
            return
        p_idx, c_idx, s_idx = map(int, self.current_node[1:])
        section = self.project["parts"][p_idx]["chapters"][c_idx]["sections"][s_idx]
        if not messagebox.askyesno("Delete section", f"Delete '{section['title']}'?"):
            return
        del self.project["parts"][p_idx]["chapters"][c_idx]["sections"][s_idx]
        self.dirty = True
        self._populate_tree()
        self._update_title()

    def find_in_editor(self) -> None:
        query = simpledialog.askstring("Find", "Find text in current Draft Text editor:")
        if not query:
            return
        self.draft_text.tag_remove("find", "1.0", "end")
        start = "1.0"
        count = 0
        while True:
            pos = self.draft_text.search(query, start, stopindex="end", nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            self.draft_text.tag_add("find", pos, end)
            start = end
            count += 1
        self.draft_text.tag_config("find", background="yellow", foreground="black")
        self.status_var.set(f"Found {count} occurrence(s) of '{query}'.")

    def copy_ai_instructions(self) -> None:
        self._sync_static_panels()
        text = self.project["author_voice_instructions"]
        self.clipboard_clear()
        self.clipboard_append(text)
        self.status_var.set("Author / LLM instructions copied to clipboard.")

    def _selected_context_text(self) -> str:
        self.commit_editor()
        if not self.current_node:
            return ""
        title, obj, body_key, notes_key = self._get_node_data(self.current_node)
        body = obj.get(body_key, "")
        notes = obj.get(notes_key, "") if notes_key else ""
        return f"SELECTED ITEM: {title}\n\nCURRENT DRAFT:\n{body}\n\nDEVELOPMENT NOTES:\n{notes}"

    def _all_section_paths(self) -> List[Tuple[int, int, int]]:
        paths: List[Tuple[int, int, int]] = []
        for p_idx, part in enumerate(self.project.get("parts", [])):
            for c_idx, chapter in enumerate(part.get("chapters", [])):
                for s_idx, _section in enumerate(chapter.get("sections", [])):
                    paths.append((p_idx, c_idx, s_idx))
        return paths

    def _find_next_available_section(self) -> Optional[Tuple[int, int, int]]:
        self.commit_editor()
        for p_idx, c_idx, s_idx in self._all_section_paths():
            section = self.project["parts"][p_idx]["chapters"][c_idx]["sections"][s_idx]
            if not section.get("body", "").strip():
                return (p_idx, c_idx, s_idx)
        return None

    def _section_sequence_context(self, path: Tuple[int, int, int]) -> Tuple[str, str]:
        paths = self._all_section_paths()
        try:
            idx = paths.index(path)
        except ValueError:
            return "None", "None"

        def label(other: Tuple[int, int, int]) -> str:
            p, c, sec = other
            chapter = self.project["parts"][p]["chapters"][c]
            section = chapter["sections"][sec]
            return f"{chapter['title']} -> {section['title']}"

        previous = label(paths[idx - 1]) if idx > 0 else "None - this is the first manuscript section."
        following = label(paths[idx + 1]) if idx + 1 < len(paths) else "None - this is the final manuscript section."
        return previous, following

    def _illustrations_for_section(self, path: Tuple[int, int, int]) -> List[str]:
        p_idx, c_idx, s_idx = path
        chapter = self.project["parts"][p_idx]["chapters"][c_idx]
        section = chapter["sections"][s_idx]
        chapter_number_match = re.match(r"\s*(\d+)\.", chapter.get("title", ""))
        chapter_number = int(chapter_number_match.group(1)) if chapter_number_match else c_idx + 1
        plan = self.project.get("chapter_illustration_plan", CHAPTER_ILLUSTRATION_PLAN)
        candidates = list(plan.get(chapter_number, plan.get(str(chapter_number), [])))

        # Put especially relevant chapter figures first, while still giving the LLM the full
        # chapter figure plan so it does not collapse the illustration program over time.
        terms = set(re.findall(r"[a-z0-9]+", section.get("title", "").lower()))
        scored = []
        for figure in candidates:
            figure_terms = set(re.findall(r"[a-z0-9]+", figure.lower()))
            score = len(terms & figure_terms)
            scored.append((score, figure))
        scored.sort(key=lambda item: (-item[0], candidates.index(item[1])))
        return [figure for _score, figure in scored]

    def _make_section_brief(self, path: Tuple[int, int, int], task_wording: str) -> str:
        self._sync_static_panels()
        p_idx, c_idx, s_idx = path
        part = self.project["parts"][p_idx]
        chapter = part["chapters"][c_idx]
        section = chapter["sections"][s_idx]
        previous, following = self._section_sequence_context(path)
        figures = self._illustrations_for_section(path)
        source_names = [src.get("name", Path(src.get("path", "")).name) for src in self.project.get("reference_sources", [])]
        source_text = "\n".join(f"- {name}" for name in source_names) if source_names else "- No reference PDFs are registered yet."
        figure_text = "\n".join(f"- {item}" for item in figures) if figures else "- No chapter-specific figure has been assigned yet; recommend one if the material needs it."

        return (
            self.project["author_voice_instructions"]
            + "\n\n--- BOOK / TARGET CONTEXT ---\n"
            + f"BOOK: {self.project['metadata'].get('title', '')}\n"
            + f"SUBTITLE: {self.project['metadata'].get('subtitle', '')}\n"
            + f"REFERENCE BUILD: {self.project['metadata'].get('reference_build', '')}\n"
            + f"PART: {part['title']}\n"
            + f"CHAPTER: {chapter['title']}\n"
            + f"SECTION: {section['title']}\n"
            + f"TARGET PATH (zero-based): {p_idx}/{c_idx}/{s_idx}\n"
            + f"PREVIOUS SECTION: {previous}\n"
            + f"NEXT SECTION: {following}\n\n"
            + "CHAPTER DEVELOPMENT NOTES:\n"
            + chapter.get("notes", "")
            + "\n\nSECTION DEVELOPMENT NOTES / REQUIRED COVERAGE:\n"
            + section.get("notes", "")
            + "\n\nCURRENT SECTION DRAFT:\n"
            + (section.get("body", "").strip() or "[EMPTY - this section has not been written yet]")
            + "\n\nCHAPTER ILLUSTRATION NEEDS RELEVANT TO THIS SECTION:\n"
            + figure_text
            + "\n\nREGISTERED PROJECT SOURCES:\n"
            + source_text
            + "\n\n--- TASK ---\n"
            + task_wording.strip()
            + "\n\nWrite only this section. Do not write the following section or repeat material that belongs there. "
              "Make the section useful to a builder, and preserve the distinction between verified geometry, documented build experience, design variations, experimental concepts, and safety/engineering issues. "
              "If a fact requires research or a dimension has not been verified, put that need in Development Notes instead of inventing an answer.\n\n"
            + "--- REQUIRED RETURN FORMAT ---\n"
            + "Return one complete import envelope exactly in this structure. Text before or after the envelope is unnecessary.\n\n"
            + f"{LLM_BEGIN_MARKER}\n"
            + f"SCHEMA={LLM_RESPONSE_SCHEMA}\n"
            + f"TARGET_PATH={p_idx}/{c_idx}/{s_idx}\n"
            + f"CHAPTER_TITLE={chapter['title']}\n"
            + f"TARGET_TITLE={section['title']}\n"
            + f"{LLM_DRAFT_MARKER}\n"
            + "[Put the finished manuscript prose for this section here. Do not include these bracketed instructions.]\n"
            + f"{LLM_NOTES_MARKER}\n"
            + "[Put only unresolved research needs, source needs, figure/table requests, verification items, or author decisions here. Use [FIGURE:], [TABLE:], [SOURCE NEEDED:], [VERIFY:], or [AUTHOR INPUT NEEDED:] markers where useful. If none, write NONE.]\n"
            + f"{LLM_END_MARKER}\n"
        )

    def _select_section_path(self, path: Tuple[int, int, int]) -> None:
        p_idx, c_idx, s_idx = path
        iid = f"section:{p_idx}:{c_idx}:{s_idx}"
        if not self.tree.exists(iid):
            self._populate_tree()
        self.tree.selection_set(iid)
        self.tree.focus(iid)
        self.tree.see(iid)
        self._load_node(("section", str(p_idx), str(c_idx), str(s_idx)))

    def copy_next_section_brief(self) -> None:
        path = self._find_next_available_section()
        if path is None:
            messagebox.showinfo("Next section", "Every section currently contains manuscript text.")
            return
        p_idx, c_idx, s_idx = path
        chapter = self.project["parts"][p_idx]["chapters"][c_idx]
        section = chapter["sections"][s_idx]
        brief = self._make_section_brief(
            path,
            "Write the next available section of the book as finished manuscript prose using all supplied requirements and context.",
        )
        self.clipboard_clear()
        self.clipboard_append(brief)
        self.last_llm_target = path
        self._select_section_path(path)
        self.upload_target_var.set(f"Awaiting response for: {chapter['title']} -> {section['title']}  [{p_idx}/{c_idx}/{s_idx}]")
        self.status_var.set(f"Next-section brief copied: {chapter['title']} -> {section['title']}")

    def copy_selected_brief(self) -> None:
        self.commit_editor()
        if not self.current_node or self.current_node[0] != "section":
            messagebox.showinfo("LLM brief", "Select a manuscript section first, or use Write Next Section.")
            return
        path = tuple(int(x) for x in self.current_node[1:4])
        p_idx, c_idx, s_idx = path
        chapter = self.project["parts"][p_idx]["chapters"][c_idx]
        section = chapter["sections"][s_idx]
        task = (
            "Develop or revise this selected section as finished manuscript prose. Preserve verified technical detail and existing useful content."
            if section.get("body", "").strip()
            else "Write this selected section as finished manuscript prose using all supplied requirements and context."
        )
        brief = self._make_section_brief(path, task)
        self.clipboard_clear()
        self.clipboard_append(brief)
        self.last_llm_target = path
        self.upload_target_var.set(f"Awaiting response for: {chapter['title']} -> {section['title']}  [{p_idx}/{c_idx}/{s_idx}]")
        self.status_var.set("Selected-section importable LLM brief copied to clipboard.")

    def show_llm_upload(self) -> None:
        self.right_tabs.select(1)
        self.upload_text.focus_set()

    def clear_llm_upload(self) -> None:
        self.upload_text.delete("1.0", "end")
        self.upload_target_var.set("No LLM response loaded.")

    def paste_llm_response(self) -> None:
        try:
            text = self.clipboard_get()
        except tk.TclError:
            messagebox.showinfo("LLM Upload", "The clipboard does not contain text.")
            return
        self.upload_text.delete("1.0", "end")
        self.upload_text.insert("1.0", text)
        self._inspect_upload_target()
        self.show_llm_upload()

    def load_llm_response_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Load LLM Section Response",
            filetypes=[("LLM response text", "*.txt *.md *.markdown"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = Path(path).read_text(encoding="utf-8-sig")
        except Exception as exc:
            messagebox.showerror("Load response failed", str(exc))
            return
        self.upload_text.delete("1.0", "end")
        self.upload_text.insert("1.0", text)
        self._inspect_upload_target()
        self.show_llm_upload()

    def _inspect_upload_target(self) -> None:
        text = self.upload_text.get("1.0", "end-1c")
        try:
            payload = parse_llm_section_response(text)
            p_idx, c_idx, s_idx = payload["target_path"]
            chapter = self.project["parts"][p_idx]["chapters"][c_idx]
            section = chapter["sections"][s_idx]
            self.upload_target_var.set(f"Detected: {chapter['title']} -> {section['title']}  [{p_idx}/{c_idx}/{s_idx}]")
        except Exception as exc:
            self.upload_target_var.set(f"Response not ready to import: {exc}")

    def insert_llm_response(self) -> None:
        self.commit_editor()
        text = self.upload_text.get("1.0", "end-1c")
        if not text.strip():
            messagebox.showinfo("LLM Upload", "Paste a response or load a response file first.")
            return
        try:
            payload = parse_llm_section_response(text)
            p_idx, c_idx, s_idx = payload["target_path"]
            chapter = self.project["parts"][p_idx]["chapters"][c_idx]
            section = chapter["sections"][s_idx]
        except (IndexError, KeyError):
            messagebox.showerror("Import failed", "The response target path does not exist in this project.")
            return
        except Exception as exc:
            messagebox.showerror("Import failed", str(exc))
            return

        expected_title = section.get("title", "").strip()
        returned_title = payload.get("target_title", "").strip()
        if returned_title.casefold() != expected_title.casefold():
            messagebox.showerror(
                "Target mismatch",
                f"The response says it belongs to:\n{returned_title}\n\n"
                f"But project path {p_idx}/{c_idx}/{s_idx} is:\n{expected_title}\n\n"
                "Nothing was inserted.",
            )
            return

        existing = section.get("body", "").strip()
        if existing:
            if not messagebox.askyesno(
                "Replace existing section?",
                f"'{expected_title}' already contains manuscript text. Replace it with this imported response?",
            ):
                return

        section["body"] = payload["draft_text"].strip()
        returned_notes = payload.get("development_notes_append", "").strip()
        if returned_notes and returned_notes.upper() != "NONE":
            stamp = "\n\n--- LLM DEVELOPMENT RETURN ---\n"
            if stamp.strip() not in section.get("notes", ""):
                section["notes"] = section.get("notes", "").rstrip() + stamp + returned_notes
            else:
                section["notes"] = section.get("notes", "").rstrip() + "\n" + returned_notes

        self.dirty = True
        self.last_llm_target = (p_idx, c_idx, s_idx)
        self._select_section_path((p_idx, c_idx, s_idx))
        self.upload_target_var.set(f"Inserted: {chapter['title']} -> {section['title']}")
        self.status_var.set(f"LLM response inserted into '{section['title']}'.")
        messagebox.showinfo(
            "Section inserted",
            f"Inserted manuscript text into:\n{chapter['title']}\n{section['title']}\n\n"
            "Any returned development items were appended to Development Notes.",
        )

    def open_reference_pdf(self) -> None:
        if fitz is None or Image is None or ImageTk is None:
            messagebox.showerror(
                "Missing dependency",
                "PDF reading requires PyMuPDF and Pillow.\n\nInstall with:\n  py -3.12 -m pip install pymupdf pillow",
            )
            return
        path = filedialog.askopenfilename(title="Open Reference PDF", filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")])
        if not path:
            return
        try:
            if self.pdf_doc is not None:
                self.pdf_doc.close()
            self.pdf_doc = fitz.open(path)
            self.pdf_path = Path(path)
            self.pdf_page_index = 0
            self.right_tabs.select(3)
            self.render_pdf_page()
            self.status_var.set(f"Reference PDF: {self.pdf_path.name}")
        except Exception as exc:
            messagebox.showerror("PDF open failed", str(exc))

    def render_pdf_page(self) -> None:
        if not self.pdf_doc:
            return
        self.pdf_page_index = max(0, min(self.pdf_page_index, len(self.pdf_doc) - 1))
        page = self.pdf_doc[self.pdf_page_index]
        matrix = fitz.Matrix(self.pdf_zoom, self.pdf_zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        mode = "RGB" if pix.n < 4 else "RGBA"
        image = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
        self.pdf_photo = ImageTk.PhotoImage(image)
        self.pdf_canvas.delete("all")
        self.pdf_canvas.create_image(0, 0, image=self.pdf_photo, anchor="nw")
        self.pdf_canvas.configure(scrollregion=(0, 0, pix.width, pix.height))
        self.page_label.configure(text=f"Page {self.pdf_page_index + 1} / {len(self.pdf_doc)}")

    def pdf_prev(self) -> None:
        if self.pdf_doc and self.pdf_page_index > 0:
            self.pdf_page_index -= 1
            self.render_pdf_page()

    def pdf_next(self) -> None:
        if self.pdf_doc and self.pdf_page_index < len(self.pdf_doc) - 1:
            self.pdf_page_index += 1
            self.render_pdf_page()

    def pdf_zoom_in(self) -> None:
        if self.pdf_doc:
            self.pdf_zoom = min(3.0, self.pdf_zoom + 0.2)
            self.render_pdf_page()

    def pdf_zoom_out(self) -> None:
        if self.pdf_doc:
            self.pdf_zoom = max(0.4, self.pdf_zoom - 0.2)
            self.render_pdf_page()

    def append_pdf_page_text(self) -> None:
        if not self.pdf_doc:
            messagebox.showinfo("PDF text", "Open a reference PDF first.")
            return
        if not self.current_node:
            return
        page = self.pdf_doc[self.pdf_page_index]
        text = page.get_text("text").strip()
        if not text:
            text = "[No extractable text found on this PDF page.]"
        header = f"\n\n--- PDF REFERENCE: {self.pdf_path.name}, page {self.pdf_page_index + 1} ---\n"
        self.notes_text.insert("end", header + text)
        self.dirty = True
        self.status_var.set("PDF page text appended to Development Notes.")

    def add_pdf_to_source_list(self) -> None:
        if not self.pdf_path:
            messagebox.showinfo("Source list", "Open a reference PDF first.")
            return
        item = {
            "path": str(self.pdf_path),
            "name": self.pdf_path.name,
        }
        sources = self.project.setdefault("reference_sources", [])
        if not any(s.get("path") == item["path"] for s in sources):
            sources.append(item)
            self.dirty = True
        self.status_var.set(f"Added {self.pdf_path.name} to project source list.")

    def _pdf_page_size(self) -> Tuple[float, float]:
        size = self.project.get("metadata", {}).get("print_size", "8.5x11")
        if size == "6x9":
            return (6 * rl_inch, 9 * rl_inch)
        if size == "8x10":
            return (8 * rl_inch, 10 * rl_inch)
        return (8.5 * rl_inch, 11 * rl_inch)

    def export_pdf(self, include_notes: bool) -> None:
        self.commit_editor()
        self._sync_static_panels()
        if BaseDocTemplate is None:
            messagebox.showerror(
                "Missing dependency",
                "PDF export requires ReportLab.\n\nInstall with:\n  py -3.12 -m pip install reportlab",
            )
            return

        suffix = "development_outline.pdf" if include_notes else "manuscript.pdf"
        path = filedialog.asksaveasfilename(
            title="Export PDF",
            defaultextension=".pdf",
            initialfile=f"the_wedge_method_{suffix}",
            filetypes=[("PDF files", "*.pdf")],
        )
        if not path:
            return

        try:
            self._build_pdf(Path(path), include_notes=include_notes)
            self.status_var.set(f"Exported {path}")
            messagebox.showinfo("Export complete", f"PDF created:\n{path}")
        except Exception as exc:
            messagebox.showerror("PDF export failed", str(exc))

    def _build_pdf(self, output_path: Path, include_notes: bool) -> None:
        pagesize = self._pdf_page_size()
        left_margin = 0.7 * rl_inch
        right_margin = 0.6 * rl_inch
        top_margin = 0.7 * rl_inch
        bottom_margin = 0.65 * rl_inch

        doc = BaseDocTemplate(
            str(output_path),
            pagesize=pagesize,
            leftMargin=left_margin,
            rightMargin=right_margin,
            topMargin=top_margin,
            bottomMargin=bottom_margin,
            title=normalize_for_reportlab(self.project["metadata"].get("title", "The Wedge Method")),
            author=normalize_for_reportlab(self.project["metadata"].get("author", "")),
        )

        frame = Frame(
            left_margin,
            bottom_margin,
            pagesize[0] - left_margin - right_margin,
            pagesize[1] - top_margin - bottom_margin,
            id="normal",
        )

        def on_page(canvas, doc_obj):
            canvas.saveState()
            canvas.setFont("Helvetica", 8)
            canvas.drawString(left_margin, 0.38 * rl_inch, normalize_for_reportlab(self.project["metadata"].get("title", "")))
            canvas.drawRightString(pagesize[0] - right_margin, 0.38 * rl_inch, str(doc_obj.page))
            canvas.restoreState()

        doc.addPageTemplates([PageTemplate(id="book", frames=[frame], onPage=on_page)])

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="BookTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=26, leading=31, alignment=TA_CENTER, spaceAfter=16))
        styles.add(ParagraphStyle(name="BookSubtitle", parent=styles["Normal"], fontName="Helvetica", fontSize=14, leading=18, alignment=TA_CENTER, spaceAfter=20))
        styles.add(ParagraphStyle(name="Part", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=20, leading=24, spaceBefore=10, spaceAfter=16))
        styles.add(ParagraphStyle(name="Chapter", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=18, leading=22, spaceBefore=8, spaceAfter=12))
        styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16, spaceBefore=10, spaceAfter=7))
        styles.add(ParagraphStyle(name="BodyBook", parent=styles["BodyText"], fontName="Times-Roman", fontSize=10.5, leading=14, spaceAfter=7))
        styles.add(ParagraphStyle(name="BulletBook", parent=styles["BodyText"], fontName="Times-Roman", fontSize=10.2, leading=13.5, leftIndent=14, firstLineIndent=-7, spaceAfter=4))
        styles.add(ParagraphStyle(name="DevNote", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.5, leading=11, textColor=colors.darkslategray, leftIndent=9, rightIndent=5, spaceAfter=5))
        styles.add(ParagraphStyle(name="SmallCenter", parent=styles["BodyText"], fontName="Helvetica", fontSize=9, leading=12, alignment=TA_CENTER))

        story = []
        meta = self.project["metadata"]
        story += [
            Spacer(1, 1.2 * rl_inch),
            Paragraph(html_escape(normalize_for_reportlab(meta.get("title", "The Wedge Method"))), styles["BookTitle"]),
            Paragraph(html_escape(normalize_for_reportlab(meta.get("subtitle", ""))), styles["BookSubtitle"]),
            Spacer(1, 0.3 * rl_inch),
            Paragraph(html_escape(normalize_for_reportlab(meta.get("author", ""))), styles["SmallCenter"]),
            Spacer(1, 0.8 * rl_inch),
            Paragraph(
                html_escape(normalize_for_reportlab("Draft development edition" if include_notes else "Manuscript draft")),
                styles["SmallCenter"],
            ),
            PageBreak(),
        ]

        story.append(Paragraph("Safety / Engineering Disclaimer", styles["Chapter"]))
        self._append_text(story, self.project["front_matter"].get("disclaimer", ""), styles, note=False)
        story.append(PageBreak())

        story.append(Paragraph("Introduction", styles["Chapter"]))
        self._append_text(story, self.project["front_matter"].get("introduction", ""), styles, note=False)
        story.append(PageBreak())

        if include_notes:
            story.append(Paragraph("Book Build-Out Elements", styles["Chapter"]))
            self._append_text(story, self.project.get("production_elements", ""), styles, note=True)
            story.append(PageBreak())
            story.append(Paragraph("Author / LLM Instructions", styles["Chapter"]))
            self._append_text(story, self.project.get("author_voice_instructions", ""), styles, note=True)
            story.append(PageBreak())

        for part in self.project["parts"]:
            story.append(Paragraph(html_escape(normalize_for_reportlab(part["title"])), styles["Part"]))
            if part.get("body", "").strip():
                self._append_text(story, part["body"], styles, note=False)
            if include_notes and part.get("notes", "").strip():
                story.append(Paragraph("Development Notes", styles["Section"]))
                self._append_text(story, part["notes"], styles, note=True)
            story.append(PageBreak())

            for chapter in part["chapters"]:
                story.append(Paragraph(html_escape(normalize_for_reportlab(chapter["title"])), styles["Chapter"]))
                if chapter.get("body", "").strip():
                    self._append_text(story, chapter["body"], styles, note=False)
                if include_notes and chapter.get("notes", "").strip():
                    story.append(Paragraph("Chapter Development Notes", styles["Section"]))
                    self._append_text(story, chapter["notes"], styles, note=True)

                for section in chapter["sections"]:
                    story.append(Paragraph(html_escape(normalize_for_reportlab(section["title"])), styles["Section"]))
                    if section.get("body", "").strip():
                        self._append_text(story, section["body"], styles, note=False)
                    elif not include_notes:
                        # Preserve the section heading in manuscript export without inserting fake prose.
                        story.append(Paragraph("[Section draft not yet written.]", styles["DevNote"]))
                    if include_notes and section.get("notes", "").strip():
                        self._append_text(story, section["notes"], styles, note=True)
                story.append(PageBreak())

        doc.build(story)

    def _append_text(self, story: List[Any], text: str, styles: Dict[str, Any], note: bool) -> None:
        text = normalize_for_reportlab(text)
        for block in text_to_paragraphs(text):
            stripped = block.strip()
            if not stripped:
                continue
            if stripped.startswith(("- ", "* ")):
                bullet = stripped[2:].strip()
                story.append(Paragraph("- " + html_escape(bullet), styles["DevNote"] if note else styles["BulletBook"]))
            else:
                # Preserve line breaks inside a paragraph.
                safe = html_escape(stripped).replace("\n", "<br/>")
                story.append(Paragraph(safe, styles["DevNote"] if note else styles["BodyBook"]))

    def on_close(self) -> None:
        if not self.maybe_save():
            return
        if self.pdf_doc is not None:
            try:
                self.pdf_doc.close()
            except Exception:
                pass
        self.destroy()


def main() -> None:
    app = BookBuilderApp()
    app.mainloop()


if __name__ == "__main__":
    main()

"""The knowledge base: a machine-readable spec of the project, generated
from the repo itself so it can never drift from the code.

``sync_knowledge()`` calls the repo's own menu/dump functions
(``lesson_menu()``, ``preset_menu()``, ``token_report()``, the object
catalog, the lexicon catalogue, ...) and folds them into one JSON
document.  That document is the "project understanding" an LLM would
otherwise spend thousands of inference tokens reconstructing.

Every section is independent: a failure in one (e.g. a module not
importable in this interpreter) is recorded in the spec and does not
stop the others.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from .config import KB_PATH, REPO_ROOT

# Imported lazily inside each section so one bad import cannot sink the sync.
_SECTIONS: tuple[str, ...] = (
    "repo",
    "tools",
    "lessons",
    "presets",
    "deliverables",
    "presenter_objects",
    "focus_targets",
    "book_tokens",
    "lexicon",
    "facts",
    "stills",
    "rules",
)


def _ensure_repo_on_path() -> None:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))


def _sec(name: str, ok: bool, data, error: str = "") -> dict:
    return {
        "section": name,
        "ok": ok,
        "data": data,
        "error": error,
    }


def _section_repo() -> dict:
    """Which checkout this spec was taken from.

    A knowledge base with no provenance is indistinguishable from a stale one,
    so the commit and the working-tree state travel with it. Never fails: a
    checkout without git is normal, not an error.
    """
    import subprocess

    info: dict = {"root": str(REPO_ROOT)}
    for key, args in (("commit", ["rev-parse", "HEAD"]),
                      ("branch", ["rev-parse", "--abbrev-ref", "HEAD"])):
        try:
            done = subprocess.run(["git", *args], cwd=str(REPO_ROOT),
                                  capture_output=True, text=True, timeout=15)
            info[key] = done.stdout.strip() if done.returncode == 0 else ""
        except (OSError, subprocess.SubprocessError):
            info[key] = ""
    try:
        done = subprocess.run(["git", "status", "--porcelain"],
                              cwd=str(REPO_ROOT), capture_output=True,
                              text=True, timeout=30)
        info["dirty_files"] = (len([l for l in done.stdout.splitlines() if l.strip()])
                               if done.returncode == 0 else None)
    except (OSError, subprocess.SubprocessError):
        info["dirty_files"] = None
    return _sec("repo", True, info)


def _section_tools() -> dict:
    """The ticket tool/action matrix.

    Hand-kept (it is the stable contract documented in the utilization guide),
    but every script named here is checked against the disk, so a renamed or
    deleted tool shows up as a failing section instead of an error hours later
    inside a recipe.
    """
    return _verify_scripts({
        "two_v_masterclass": {
            "script": "two_v_masterclass.py",
            "actions": ["run", "selftest", "report", "shots", "export_video",
                        "render_beats", "voice_preview", "list_voices",
                        "narration_only", "script", "build_packet",
                        "list_lessons", "list_deliverables", "list_segments",
                        "soundboard", "render_all"],
        },
        "presenter": {
            "script": "presenter_studio.py",
            "actions": ["run", "compose", "shots", "export", "export_all",
                        "selftest", "save_json"],
        },
        "dome_forge": {
            "script": "dome_forge.py",
            "actions": ["run", "selftest", "shots"],
        },
        "assembly_line": {
            "script": "assembly_line.py",
            "actions": ["run", "selftest", "shots"],
        },
        "dome_composer": {
            "script": "dome_composer.py",
            "actions": ["run", "shots", "report", "selftest"],
        },
        "raw_wedge_dome": {
            "script": "geodesic_raw_wedge_dome_dihedral.py",
            "actions": ["run", "validate", "fabrication", "extract_resources"],
        },
        "book_studio": {
            "script": "book_studio.py",
            "actions": ["studio", "read_html", "read_pdf", "outline", "audit",
                        "progress", "scaffold", "render_figures", "export",
                        "selftest"],
        },
    })


def _verify_scripts(matrix: dict) -> dict:
    """Mark each tool with whether its script is actually on disk."""
    missing: list[str] = []
    for name, entry in matrix.items():
        script = REPO_ROOT / str(entry.get("script", ""))
        entry["present"] = script.is_file()
        if not entry["present"]:
            missing.append(f"{name} ({entry.get('script')})")
    if missing:
        return _sec("tools", False, matrix,
                    "scripts missing from the checkout: " + ", ".join(missing))
    return _sec("tools", True, matrix)


def _section_lessons() -> dict:
    _ensure_repo_on_path()
    try:
        from two_v_demo.lesson_registry import LESSONS, lesson_menu
        data = {
            key: {
                "title": lesson.title,
                "chapters": len(lesson.chapters),
                "snapshot_prefix": getattr(lesson, "snapshot_prefix", "lesson"),
                "style": getattr(lesson, "style", "teaching"),
                "voice_rate": getattr(lesson, "voice_rate", None),
                "brand": getattr(lesson, "brand", ""),
            }
            for key, lesson in LESSONS.items()
        }
        data["_menu"] = lesson_menu()
        return _sec("lessons", True, data)
    except Exception as exc:  # noqa: BLE001
        return _sec("lessons", False, None, f"{type(exc).__name__}: {exc}")


def _section_presets() -> dict:
    _ensure_repo_on_path()
    try:
        from render_presets import PRESET_BY_KEY
        data = {
            key: {"label": preset.label, "summary": preset.summary,
                  "fields": preset.applied()}
            for key, preset in PRESET_BY_KEY.items()
        }
        return _sec("presets", True, data)
    except Exception as exc:  # noqa: BLE001
        return _sec("presets", False, None, f"{type(exc).__name__}: {exc}")


def _section_deliverables() -> dict:
    _ensure_repo_on_path()
    try:
        from two_v_demo.deliverables import DELIVERABLES, deliverables_menu
        data = {
            item.filename: {"lesson": item.lesson, "note": item.note,
                            "built": item.path().is_file()}
            for item in DELIVERABLES
        }
        data["_menu"] = deliverables_menu()
        return _sec("deliverables", True, data)
    except Exception as exc:  # noqa: BLE001
        return _sec("deliverables", False, None, f"{type(exc).__name__}: {exc}")


def _section_presenter_objects() -> dict:
    _ensure_repo_on_path()
    try:
        from presenter.library import OBJECT_SPECS
        data = {
            spec.key: {
                "label": spec.label,
                "category": spec.category,
                "blurb": spec.blurb,
                "params": {
                    p.key: {"label": p.label, "default": p.default,
                            "low": p.low, "high": p.high, "step": p.step,
                            "choices": p.choices, "unit": p.unit}
                    for p in spec.params
                },
            }
            for spec in OBJECT_SPECS
        }
        return _sec("presenter_objects", True, data)
    except Exception as exc:  # noqa: BLE001
        return _sec("presenter_objects", False, None, f"{type(exc).__name__}: {exc}")


def _section_focus_targets() -> dict:
    _ensure_repo_on_path()
    try:
        from presenter.world import all_emitters
        names = sorted(set(all_emitters().keys()))
        return _sec("focus_targets", True, {
            "names": names,
            "note": ("registered by the world/accessory/forge emitters; the "
                     "camera can follow any of these by name"),
        })
    except Exception as exc:  # noqa: BLE001
        return _sec("focus_targets", False, None, f"{type(exc).__name__}: {exc}")


def _section_book_tokens() -> dict:
    _ensure_repo_on_path()
    try:
        from two_v_demo.book_tokens import token_map
        data = {
            name: {"describe": token.describe, "value": token.value()}
            for name, token in sorted(token_map().items())
        }
        return _sec("book_tokens", True, data)
    except Exception as exc:  # noqa: BLE001
        return _sec("book_tokens", False, None, f"{type(exc).__name__}: {exc}")


def _section_lexicon() -> dict:
    _ensure_repo_on_path()
    try:
        from two_v_demo import lexicon
        from two_v_demo import visual_objects
        data = {
            "terms": {k: {"define": v.define, "visual": v.visual,
                          "icon": v.icon, "rendering": lexicon.rendering(v)}
                      for k, v in lexicon.term_map().items()},
            "visual_objects": sorted(visual_objects.registry().keys()),
        }
        return _sec("lexicon", True, data)
    except Exception as exc:  # noqa: BLE001
        return _sec("lexicon", False, None, f"{type(exc).__name__}: {exc}")


def _section_facts() -> dict:
    try:
        from .facts import FACT_SPECS
        data = {fid: {"description": spec.description,
                      "params": {k: getattr(v, "__name__", str(v))
                                 for k, v in (spec.params or {}).items()}}
                for fid, spec in FACT_SPECS.items()}
        return _sec("facts", True, data)
    except Exception as exc:  # noqa: BLE001
        return _sec("facts", False, None, f"{type(exc).__name__}: {exc}")


def _section_stills() -> dict:
    return _sec("stills", True, {
        "masterclass": "ticket two_v_masterclass {action:'shots', lesson, shots:'t1,t2'} -> two_v_demo_output/<lesson>/<prefix>_<t:07.2f>s.png",
        "presenter": "ticket presenter {action:'shots', demo|script, shots} -> deliverables/presenter/shot_<t:07.1f>s.png",
        "dome_forge": "ticket dome_forge {action:'shots', shot_dir} -> exterior/cutaway/top/ground.png",
        "assembly_line": "ticket assembly_line {action:'shots', shots, shot_speed, seed} -> <shot_dir>/shot_<t:07.1f>s.png",
        "dome_composer": "ticket dome_composer {action:'shots', shots_dir} -> turntable 4 PNGs",
        "book_figures": "book_figures.render_all -> deliverables/book/figures/*.png",
    })


def _section_rules() -> dict:
    return _sec("rules", True, {
        "numbers": "every on-screen number is computed by code that proves it; borrowed values are named external constants with unit + source, printed in the report",
        "determinism": "seed every random generator; frames are pure functions of (stage, progress)",
        "reuse": "reuse segments/figure/timber/visual_objects/lexicon and the bridges before drawing anything new",
        "stills_first": "render one still per chapter/scene and look at every one before exporting",
        "verify": "verify by frame count (nb_frames ~ duration*fps), not by duration alone",
        "append_only": "rendered output is append-only; re-renders land beside the old cut as -v2/-v3",
        "corrections": "corrections are chapters on camera, not silent re-cuts",
        "sequential": "never run voiced exports in parallel (speech endpoint throttles)",
        "camera_traps": "lay rows along X (+X is screen left at yaw 90); distance ~2x object size; keep the left third clear in teaching style; nothing straddles z=0",
    })


def sync_knowledge(write: bool = True) -> dict:
    """Rebuild the project spec from the repo and return it.

    With ``write=True`` the spec is saved to :data:`config.KB_PATH`.
    """
    sections: dict[str, dict] = {}
    for name in _SECTIONS:
        sections[name] = globals()[f"_section_{name}"]()
    spec = {
        "schema": "project-agent-spec/1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "repo_root": str(REPO_ROOT),
        "sections": sections,
    }
    if write:
        KB_PATH.parent.mkdir(parents=True, exist_ok=True)
        KB_PATH.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    return spec


def load_kb() -> dict:
    if KB_PATH.is_file():
        return json.loads(KB_PATH.read_text(encoding="utf-8"))
    return sync_knowledge(write=True)


def kb_summary(spec: dict) -> str:
    """A compact text digest of the spec, for system prompts and status."""
    lines: list[str] = []
    for name, section in spec["sections"].items():
        if not section["ok"]:
            lines.append(f"{name}: FAILED ({section['error']})")
            continue
        data = section["data"]
        if name == "lessons":
            n = len(data) - 1
            lines.append(f"lessons: {n} registered ({', '.join(sorted(k for k in data if not k.startswith('_')))[:200]})")
        elif name == "presets":
            lines.append(f"presets: {len(data)}")
        elif name == "deliverables":
            built = sum(1 for d in data.values() if isinstance(d, dict) and d.get("built"))
            lines.append(f"deliverables: {built} built of {len(data) - 1}")
        elif name == "presenter_objects":
            lines.append(f"presenter objects: {len(data)} ({', '.join(sorted(data))[:200]})")
        elif name == "focus_targets":
            lines.append(f"focus targets: {len(data['names'])}")
        elif name == "book_tokens":
            lines.append(f"book tokens: {len(data)}")
        elif name == "lexicon":
            lines.append(f"lexicon: {len(data['terms'])} terms, {len(data['visual_objects'])} visual objects")
        elif name == "facts":
            lines.append(f"facts: {', '.join(sorted(data))}")
        else:
            lines.append(f"{name}: ok")
    return "\n".join(lines)

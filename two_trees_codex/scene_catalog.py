"""Read-only language index of the existing films for the Codex book.

No painter, validation callback, camera callback, window or audio service is
started to build this index. Imports run in a bounded subprocess with graphics
imports blocked. Authored terms/concepts remain attributed to their source;
matching is a deterministic editorial suggestion, not a claim of NLP completeness.

    python -m two_trees_codex.scene_catalog --output-dir two_trees_codex/workspace/catalogs
    python -m two_trees_codex.scene_catalog --query "Eight sections, eight wedges each"
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import importlib
import importlib.abc
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
import uuid

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parent
SCHEMA = "two-trees-codex-scene-catalog/v1"
_MARKER = "CODEX_SCENE_CATALOG_JSON:"
_STOP = frozenset("a an and are as at be been being by can could do does each for from had has have how i if in into is it its let me more most my next no not of on one only or our out over same so some than that the their them then there these they this those through to too two up us use used using very was we were what when where which while who will with would you your".split())
_CACHE = None
_CACHE_FINGERPRINT = None


def _plain(value):
    return " ".join(str(value or "").split())


@lru_cache(maxsize=8192)
def _tokens(text):
    """Small, explicit lexical normalization; no semantic or POS model."""
    text = unicodedata.normalize("NFKC", str(text)).lower().replace("’", "'")
    result = []
    irregular = {"feet": "foot", "indices": "index", "vertices": "vertex",
                 "axes": "axis", "people": "person", "halves": "half"}
    for word in re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text):
        if word.endswith("'s"):
            word = word[:-2]
        if word in irregular:
            word = irregular[word]
        elif len(word) > 4 and word.endswith("ies"):
            word = word[:-3] + "y"
        elif len(word) > 4 and word.endswith(("sses", "shes", "ches", "xes")):
            word = word[:-2]
        elif len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is", "ics", "ous")):
            word = word[:-1]
        result.append(word)
    return tuple(result)


@lru_cache(maxsize=8192)
def _phrase(text):
    return " " + " ".join(_tokens(text)) + " "


def _contains(haystack, needle):
    return bool(_tokens(needle)) and _phrase(needle) in _phrase(haystack)


def _excerpt(text, words, limit=230):
    text = _plain(text)
    low = text.casefold()
    starts = [low.find(word.casefold()) for word in words if word and low.find(word.casefold()) >= 0]
    start = max(0, (min(starts) if starts else 0) - 55)
    stop = min(len(text), start + limit)
    return ("…" if start else "") + text[start:stop] + ("…" if stop < len(text) else "")


def _source_file(path):
    path = Path(path).resolve()
    try:
        raw = path.read_bytes()
        return {"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(raw).hexdigest()}
    except (OSError, ValueError):
        return {"path": str(path), "sha256": ""}


def _fingerprint():
    files = sorted((ROOT / "two_v_demo").glob("lesson*.py"))
    files += sorted((ROOT / "two_v_demo").glob("lexicon*.py"))
    files += [ROOT / "two_v_demo" / "book_math.py", ROOT / "two_v_demo" / "book_tokens.py",
              ROOT / "two_v_demo" / "visual_objects.py", ROOT / "two_v_demo" / "visuals_forest.py"]
    return tuple((str(path), path.stat().st_mtime_ns, path.stat().st_size) for path in files if path.exists())


class _NoGraphics(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"moderngl", "pygame", "pyglet", "OpenGL", "glfw", "tkinter"} or fullname == "two_v_demo.app":
            raise ImportError(f"Graphics import blocked while indexing: {fullname}")
        return None


def _default_progress(lesson_key, chapter):
    chosen = {"harvest:tree": 0.18, "harvest:fell": 0.62,
              "harvest:explode": 0.88, "harvest:why": 0.78,
              "harvest:assume": 0.95, "harvest:cost": 0.93}
    return chosen.get(f"{lesson_key}:{chapter.slug}", 0.94 if chapter.overlay == "math" else 0.72)


def _lesson_rows(lesson, module_name):
    scenes = []
    for index, chapter in enumerate(lesson.chapters):
        scene_id = f"{lesson.key}:{chapter.slug}"
        narration = [_plain(line) for line in chapter.narration]
        scene = {
            "id": scene_id, "lesson_key": str(lesson.key), "lesson_title": str(lesson.title),
            "chapter_slug": str(chapter.slug), "chapter_number": str(chapter.number),
            "chapter_index": index, "title": str(chapter.title), "stage": str(chapter.stage),
            "summary": _plain(chapter.promise), "purpose": _plain(chapter.promise),
            "narration": narration, "equations": [str(line) for line in chapter.equations],
            "duration": float(chapter.duration), "camera": [float(n) for n in chapter.camera],
            "progress": _default_progress(lesson.key, chapter),
            "progress_note": "Editorial still default; adjust the snapshot position to reveal the intended beat.",
            "camera_mode": "authored callback" if lesson.camera_fn else "authored orbit",
            "overlay": chapter.overlay or lesson.style,
            "keywords": [], "terms": [], "concepts": [],
            "source": {"ref": f"film:{lesson.key}/{chapter.slug}", "module": module_name},
        }
        scene["keywords"] = sorted({word for word in _tokens(" ".join([scene["title"], scene["summary"], *narration])) if word not in _STOP and len(word) > 2 and not word.isdigit()})
        scenes.append(scene)
    return scenes


def _metadata():
    result = {"terms": [], "concepts": [], "categories": [], "objects": [], "warnings": []}
    try:
        lexicon = importlib.import_module("two_v_demo.lexicon")
        try:
            resolve = importlib.import_module("two_v_demo.book_tokens").resolve
        except Exception as exc:
            result["warnings"].append(f"Number tokens retained: {type(exc).__name__}: {exc}")
            resolve = lambda text: text
        def resolved(text):
            try:
                return resolve(text)
            except Exception as exc:
                result["warnings"].append(f"Unresolved definition: {type(exc).__name__}: {exc}")
                return text
        for term in lexicon.terms():
            result["terms"].append({
                "key": term.key, "name": term.name, "category": term.category,
                "definition": resolved(term.define), "define": resolved(term.define),
                "definition_template": term.define, "aliases": list(term.aliases),
                "visual": term.visual, "icon": term.icon, "figures": list(term.figures),
                "scene": term.scene, "see": list(term.see), "scene_ids": [],
                "source": "two_v_demo/lexicon_terms.py", "kind": "authored term",
            })
        for concept in lexicon.concepts():
            result["concepts"].append({
                "key": concept.key, "name": concept.name, "domain": concept.domain,
                "claim": resolved(concept.claim), "explain": resolved(concept.explain),
                "caveat": resolved(concept.caveat), "terms": list(concept.terms),
                "figures": list(concept.figures), "taught": list(concept.taught),
                "recipe": list(concept.recipe), "scene_ids": [],
                "source": "two_v_demo/lexicon_concepts.py",
            })
    except Exception as exc:
        result["warnings"].append(f"Authored lexicon unavailable: {type(exc).__name__}: {exc}")
    try:
        taxonomy = importlib.import_module("two_v_demo.lexicon_taxonomy")
        for category in taxonomy.categories():
            result["categories"].append({"key": category.key, "name": category.name,
                "blurb": category.blurb, "rendering": category.rendering,
                "words": sorted(category.words), "source": "two_v_demo/lexicon_taxonomy.py"})
    except Exception as exc:
        result["warnings"].append(f"Noun categories unavailable: {type(exc).__name__}: {exc}")
    try:
        objects = importlib.import_module("two_v_demo.visual_objects").registry()
        for obj in objects.values():
            result["objects"].append({"key": obj.key, "label": obj.label,
                "category": obj.category, "summary": obj.blurb, "source": obj.source,
                "words": list(obj.words), "defaults": obj.defaults()})
    except Exception as exc:
        result["warnings"].append(f"Visual object metadata unavailable: {type(exc).__name__}: {exc}")
    return result


def _worker(mode):
    sys.dont_write_bytecode = True
    sys.meta_path.insert(0, _NoGraphics())
    if mode == "metadata":
        return _metadata()
    if mode == "inventory":
        return _noun_inventory(json.load(sys.stdin).get("scenes", []))
    module_name = "two_v_demo.lesson_registry" if mode == "registry" else mode
    module = importlib.import_module(module_name)
    if mode == "registry":
        lessons = list(module.LESSONS.values())
    else:
        # Only registered exports requested by the parent; unrelated module
        # objects are not treated as published scenes.
        names = _registry_modules().get(module_name, [])
        lessons = [getattr(module, name) for name in names if hasattr(module, name)]
    rows, seen = [], set()
    for lesson in lessons:
        if getattr(lesson, "key", None) in seen or not hasattr(lesson, "chapters"):
            continue
        seen.add(lesson.key)
        rows.extend(_lesson_rows(lesson, module_name))
    return {"scenes": rows, "lesson_keys": sorted(seen)}


def _noun_inventory(scenes):
    """Use the existing scan/classification APIs without reimporting the registry.

    Reading scene data already collected avoids a graphics import hidden in a
    legacy lesson. Other corpus readers are isolated individually. Presentations
    are omitted because their reader executes builders, not just source reads.
    """
    corpus = importlib.import_module("two_v_demo.lexicon_corpus")
    words = importlib.import_module("two_v_demo.lexicon_words")
    taxonomy = importlib.import_module("two_v_demo.lexicon_taxonomy")
    entries, titles, warnings = [], {}, []
    for scene in scenes:
        place = corpus.Place("film", scene["lesson_key"], scene["chapter_slug"], scene["title"])
        entries.extend([(place, "title", scene["title"]), (place, "headline", scene["summary"])])
        entries.append((place, "narration", " ".join(scene.get("narration", []))))
        entries.extend((place, "equation", line) for line in scene.get("equations", []))
        titles[("film", scene["lesson_key"])] = scene["lesson_title"]
    sources = ["film"]
    for source in ("segment", "book", "manuscript", "notes", "codex", "listing", "trailer"):
        try:
            source_entries, source_titles = corpus.READERS[source]()
            entries.extend(source_entries)
            titles.update({(source, key): value for key, value in source_titles.items()})
            sources.append(source)
        except Exception as exc:
            warnings.append(f"Noun source {source}: {type(exc).__name__}: {exc}")
    merged = {}
    for place, field, text in entries:
        text = _plain(text)
        if text:
            merged.setdefault((field, text), [])
            if place not in merged[(field, text)]:
                merged[(field, text)].append(place)
    passages = tuple(corpus.Passage(field, text, tuple(places)) for (field, text), places in merged.items())
    data = corpus.Corpus(passages, titles, len(entries))
    scan = words.Scan(data)
    rows = []
    for lemma, evidence in scan.evidence.items():
        category = taxonomy.category_of(lemma)
        if lemma in taxonomy.NOT_NOUNS or (category is None and words.needs_a_person(lemma)):
            continue
        noun, confidence, proper = words.classify(lemma, evidence)
        if category is None and not noun:
            continue
        forms = scan.forms[lemma]
        # Retain classification confidence and evidence, including uncertain nouns.
        passage_index = min(scan.passages[lemma])
        rows.append({"lemma": lemma, "category": category or ("Names" if proper else "Uncategorised"),
            "count": evidence.total, "spoken": scan.spoken[lemma], "passages": len(scan.passages[lemma]),
            "works": sorted(scan.works[lemma]), "forms": forms.most_common(),
            "decided_by": "taxonomy" if category else "evidence",
            "confidence": 1.0 if category else round(confidence, 3), "proper": proper,
            "example": _excerpt(data.passages[passage_index].text, list(forms)),
            "source": "two_v_demo.lexicon_words.Scan + classify; lexicon_taxonomy"})
    rows.sort(key=lambda row: (-row["count"], row["lemma"]))
    return {"nouns": rows, "warnings": warnings, "sources": sources,
            "passage_count": len(passages), "work_count": len(titles)}


def _run_worker(mode, timeout=30, payload=None):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    python = Path(sys.executable)
    if python.name.lower() == "pythonw.exe" and python.with_name("python.exe").exists():
        python = python.with_name("python.exe")
    try:
        completed = subprocess.run([str(python), "-B", "-m", "two_trees_codex.scene_catalog", "--worker", mode],
            cwd=ROOT, env=env, capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
            input=json.dumps(payload) if payload is not None else None,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if completed.returncode:
            return None, f"{mode}: " + (completed.stderr.strip().splitlines()[-1] if completed.stderr.strip() else f"exit {completed.returncode}")
        if _MARKER not in completed.stdout:
            return None, f"{mode}: metadata worker returned no JSON"
        return json.loads(completed.stdout.rsplit(_MARKER, 1)[1]), None
    except subprocess.TimeoutExpired:
        return None, f"{mode}: metadata import exceeded {timeout}s and was stopped"
    except (OSError, ValueError) as exc:
        return None, f"{mode}: {type(exc).__name__}: {exc}"


def _registry_modules():
    """Fallback discovery from current registry imports, never a fixed lesson list."""
    tree = ast.parse((ROOT / "two_v_demo" / "lesson_registry.py").read_text(encoding="utf-8-sig"))
    used = set()
    for node in ast.walk(tree):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        if any(isinstance(target, ast.Name) and target.id == "LESSONS" for target in targets):
            used.update(child.id for child in ast.walk(node.value) if isinstance(child, ast.Name))
    modules = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("lesson"):
            names = [item.name for item in node.names if item.name.endswith("_LESSON") and (not used or (item.asname or item.name) in used)]
            if names:
                modules["two_v_demo." + node.module] = names
    return modules


def _enrich(catalog):
    scenes = catalog["scenes"]
    scene_text = {s["id"]: " ".join([s["title"], s["summary"], *s.get("narration", []), *s.get("equations", [])]) for s in scenes}
    for term in catalog["terms"]:
        linked = []
        lesson, _, stage = term["scene"].partition(":")
        for scene in scenes:
            explicit = bool(stage) and scene["lesson_key"] == lesson and scene["stage"] == stage
            if explicit or any(_contains(scene_text[scene["id"]], phrase) for phrase in [term["key"], *term["aliases"]]):
                linked.append(scene["id"])
                scene["terms"].append(term["key"])
        term["scene_ids"] = linked
    for concept in catalog["concepts"]:
        linked = set()
        for ref in concept["taught"]:
            if ref.startswith("film:"):
                lesson, _, slug = ref[5:].partition("/")
                linked.add(f"{lesson}:{slug}")
        recipes = [step[6:] for step in concept["recipe"] if step.startswith("scene:")]
        for scene in scenes:
            if f"{scene['lesson_key']}/{scene['stage']}" in recipes:
                linked.add(scene["id"])
            if scene["id"] in linked:
                scene["concepts"].append(concept["key"])
        concept["scene_ids"] = sorted(linked & set(scene_text))
    # Render source provenance is finer than the registry itself.
    try:
        modules = _registry_modules()
        module_keys = {}
        for module in modules:
            path = ROOT / (module.replace(".", "/") + ".py")
            raw = path.read_text(encoding="utf-8-sig")
            for key in re.findall(r"key\s*=\s*['\"]([^'\"]+)['\"]", raw):
                module_keys.setdefault(key, module)
        for scene in scenes:
            if scene.get("source", {}).get("module") == "two_v_demo.lesson_registry":
                scene["source"]["module"] = module_keys.get(scene["lesson_key"], "two_v_demo.lesson_registry")
    except (OSError, SyntaxError):
        pass
    return catalog


def build_catalog(*, refresh=False, include_inventory=True):
    """Return JSON data without initializing graphics or modifying source files.

    A failed registry import falls back to each currently registered lesson module
    separately. Slow/crashing imports become source warnings; usable scenes survive.
    ``refresh`` rebuilds this process's cache. No disk write happens here.
    """
    global _CACHE, _CACHE_FINGERPRINT
    fingerprint = (_fingerprint(), bool(include_inventory))
    if not refresh and _CACHE is not None and fingerprint == _CACHE_FINGERPRINT:
        return json.loads(json.dumps(_CACHE))
    warnings, scenes = [], []
    payload, error = _run_worker("registry", timeout=8)
    if error:
        warnings.append(error)
        try:
            modules = _registry_modules()
        except (OSError, SyntaxError) as exc:
            modules = {}
            warnings.append(f"Registry discovery failed: {exc}")
        with ThreadPoolExecutor(max_workers=4) as pool:
            jobs = [(module, pool.submit(_run_worker, module, timeout=35)) for module in sorted(modules)]
            for module, job in jobs:
                data, error = job.result()
                if error:
                    warnings.append(error)
                elif data:
                    scenes.extend(data["scenes"])
    else:
        scenes = payload["scenes"]
    data, error = _run_worker("metadata")
    if error:
        warnings.append(error)
    metadata = data or {"terms": [], "concepts": [], "categories": [], "objects": [], "warnings": []}
    warnings.extend(metadata.pop("warnings"))
    nouns, inventory_info = [], {}
    if include_inventory:
        data, error = _run_worker("inventory", timeout=25, payload={"scenes": scenes})
        if error:
            warnings.append(error + "; authored terms and scene matching remain available")
        elif data:
            nouns = data["nouns"]
            warnings.extend(data.get("warnings", []))
            inventory_info = {key: data[key] for key in ("sources", "passage_count", "work_count") if key in data}
    scenes = sorted({s["id"]: s for s in scenes}.values(), key=lambda s: (s["lesson_key"], s["chapter_index"], s["id"]))
    catalog = {"schema": SCHEMA, "edition": "Codex parallel book", "scenes": scenes,
        **metadata, "nouns": nouns,
        "source": {"registry": "two_v_demo/lesson_registry.py", "read_only": True,
            "lesson_count": len({s["lesson_key"] for s in scenes}),
            "scene_count": len(scenes), "files": [_source_file(path) for path, _, _ in fingerprint[0]],
            "matching": "Deterministic whole-word/phrase, authored term and concept matching; scores are rankings, not probabilities.",
            "coverage": "Available registered lesson metadata and authored terms/concepts. Noun inventory uses existing corpus readers, Scan and classification APIs with the loaded films; presentation builders are excluded. Counts are deduplicated passages, not exhaustive or independently verified noun extraction.",
            "inventory_available": bool(nouns), "noun_count": len(nouns), "inventory": inventory_info, "warnings": warnings},
        "warnings": warnings,
    }
    _enrich(catalog)
    _CACHE, _CACHE_FINGERPRINT = catalog, fingerprint
    return json.loads(json.dumps(catalog))


def get_scene(scene_id, catalog=None):
    """Return the exact chapter snapshot source, or raise a helpful KeyError."""
    catalog = build_catalog() if catalog is None else catalog
    for scene in catalog.get("scenes", []):
        if scene["id"] == scene_id:
            return scene
    raise KeyError(f"Unknown book scene {scene_id!r}; use a catalog scene id (lesson:chapter)")


def suggest_scenes(text, catalog=None, limit=8):
    """Rank illustration candidates, carrying the evidence for each suggestion."""
    if limit <= 0 or not _plain(text):
        return []
    catalog = build_catalog() if catalog is None else catalog
    query = set(_tokens(text)) - _STOP
    query = {word for word in query if len(word) > 2 and not word.isdigit()}
    if not query:
        return []
    terms = {t["key"]: t for t in catalog.get("terms", [])}
    matched = {key: next((phrase for phrase in [key, term.get("name", ""), *term.get("aliases", [])] if phrase and _contains(text, phrase)), "") for key, term in terms.items()}
    matched = {key: phrase for key, phrase in matched.items() if phrase}
    scene_sets = []
    for scene in catalog.get("scenes", []):
        source_text = " ".join([scene["title"], scene.get("summary", ""), *scene.get("narration", []), *scene.get("equations", [])])
        scene_sets.append((scene, source_text, set(_tokens(source_text)) - _STOP))
    document_frequency = Counter(word for _, _, words in scene_sets for word in words)
    n = len(scene_sets)
    average_words = max(1, sum(len(words) for _, _, words in scene_sets) / max(1, n))
    # The first line supplied by the book editor is its page heading. Explicit
    # purpose there should outweigh an incidental mention late in a long page.
    heading = set(_tokens(str(text).splitlines()[0])) & query if "\n" in str(text) else set()
    concepts = {c["key"]: c for c in catalog.get("concepts", [])}
    results = []
    for scene, source_text, words in scene_sets:
        shared = sorted(query & words)
        scene_terms = sorted(set(scene.get("terms", [])) & set(matched))
        title_words = set(_tokens(scene["title"] + " " + scene.get("summary", "")))
        score = sum((1 + math.log((n + 1) / (document_frequency[word] + 1))) *
                    (2 if word in title_words else 1) * (2.5 if word in heading else 1) for word in shared)
        # Broad overview chapters otherwise win by mentioning almost everything.
        score /= 0.55 + 0.45 * (len(words) / average_words)
        reasons = []
        term_score = 0
        for key in scene_terms:
            term = terms[key]
            direct = term.get("scene") == f"{scene['lesson_key']}:{scene['stage']}"
            term_score += (7 if direct else 3) + min(3, len(_tokens(key)) - 1)
            if direct:
                reasons.append(f"Defined term “{term.get('name', key)}” maps to this scene painter ({term['scene']}).")
        score += min(28, term_score)
        concept_score = 0
        for key in scene.get("concepts", []):
            concept = concepts.get(key, {})
            named = _contains(text, concept.get("name", ""))
            related = sorted(set(concept.get("terms", [])) & set(matched))
            if named or len(related) >= 2:
                concept_score += 9 if named else min(8, len(related) * 2)
                reasons.append(f"Concept: {concept.get('name', key)}; linked by " + ("its name" if named else ", ".join(related)) + ".")
        score += min(12, concept_score)
        if heading & words:
            reasons.append("Page heading matches: " + ", ".join(sorted(heading & words)) + ".")
        if not shared and not scene_terms:
            continue
        if shared:
            reasons.append("Source wording: " + ", ".join(shared[:10]) + ".")
        evidence_terms = [matched[key] for key in scene_terms] or shared
        reasons.append("Book excerpt: “" + _excerpt(text, evidence_terms) + "”")
        reasons.append("Scene excerpt: “" + _excerpt(source_text, evidence_terms) + "”")
        results.append({"scene": scene, "score": round(score, 3),
            "matched_terms": scene_terms or shared, "reasons": reasons,
            "evidence": {"book_excerpt": _excerpt(text, evidence_terms),
                "scene_excerpt": _excerpt(source_text, evidence_terms),
                "source_ref": scene.get("source", {}).get("ref", "")}})
    return sorted(results, key=lambda row: (-row["score"], row["scene"]["id"]))[:limit]


def export_catalog(output_dir, catalog=None):
    """Create a new versioned JSON file inside the Codex edition only."""
    destination = Path(output_dir).resolve()
    if not destination.is_relative_to(PACKAGE):
        raise ValueError("Catalog exports must be inside two_trees_codex/ to preserve the parallel edition")
    catalog = build_catalog() if catalog is None else catalog
    destination.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = destination / f"scene_catalog_v1_{stamp}_{uuid.uuid4().hex[:8]}.json"
    with path.open("x", encoding="utf-8") as handle:
        json.dump(catalog, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, help="Explicit output folder inside two_trees_codex/")
    parser.add_argument("--query", help="Find still scenes for book language")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--worker", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker:
        print(_MARKER + json.dumps(_worker(args.worker), ensure_ascii=True))
        return 0
    catalog = build_catalog()
    if args.query:
        for row in suggest_scenes(args.query, catalog, args.limit):
            print(f"{row['score']:7.2f}  {row['scene']['id']}: {row['scene']['title']}")
            for reason in row["reasons"]:
                print("    " + reason)
    if args.output_dir:
        print(export_catalog(args.output_dir, catalog))
    if not args.query and not args.output_dir:
        print(f"{len(catalog['scenes'])} scenes, {len(catalog['terms'])} terms, {len(catalog['concepts'])} concepts, {len(catalog['nouns'])} catalogued nouns")
    for warning in catalog["warnings"]:
        print("Catalog note: " + warning, file=sys.stderr)
    return 0 if catalog["scenes"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

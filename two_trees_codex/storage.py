"""Versioned manuscript storage and portable, additive interchange."""
from __future__ import annotations

import base64
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path
import re
import uuid

PACKAGE = Path(__file__).resolve().parent
DEFAULT_HOME = PACKAGE / "workspace"
TITLE = "2 trees: Build your (D)Home"
SCHEMA = "two-trees-book/v1"


def stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def new_id():
    return "codex-" + uuid.uuid4().hex[:16]


def words(text):
    return len(re.findall(r"\b[\w’'-]+\b", text))


def new_page(title="Untitled page", kind="chapter", strand="how-to", body=""):
    return dict(id=new_id(), title=title, kind=kind, strand=strand,
                status="draft", body=body, notes="", figures=[])


def seed_pages():
    source = (PACKAGE / "seed.md").read_text(encoding="utf-8")
    chunks = re.split(r"<!-- page: ([\w-]+) \| ([\w-]+) \| ([\w-]+) -->\s*", source)
    pages = []
    for pos in range(1, len(chunks), 4):
        page_id, kind, strand, content = chunks[pos:pos + 4]
        title, _, body = content.strip().partition("\n")
        p = new_page(title.lstrip("# "), kind, strand, body.strip() + "\n")
        p["id"] = "codex-" + page_id
        p["status"] = "field record needed" if kind == "journal" else "draft"
        pages.append(p)
    topics = [
        ("The starting inventory", "What did the actual trees change about the initial plan?", "Measure and label the available sections; save the first configuration."),
        ("The first configuration", "Which dimension became the controlling constraint?", "Compare desired-radius and available-stock routes; record allowances."),
        ("The first useful blank", "What was different between the imagined wedge and the real one?", "Record the representative stock trial, actual losses, and setup time."),
        ("The first corner", "What did the contact between two members teach you?", "Document end-to-side contact and the cyclic pinwheel with close photographs."),
        ("A repeatable process", "Which adjustment made the next piece easier to repeat?", "Record fixture changes and separate accepted, uncertain, and rejected pieces."),
        ("The tree has a say", "Where did taper or a defect force a decision?", "Update member assignments and the remaining usable stock count."),
        ("Halfway through the clock", "What remains uncertain at the halfway point?", "Reconcile accepted members, time spent, and the work still ahead."),
        ("The first panel family", "When did loose members begin to feel like a building?", "Check the first accepted A-A-A batch against its reference geometry."),
        ("The second panel family", "What changed when the short members entered the pattern?", "Check B-A-B panels and compare their fixture and joint requirements."),
        ("Forty triangles, if ready", "What almost escaped the final panel check?", "Reconcile the actual panel count and photograph labels and spares."),
        ("Ready to assemble", "Which preparation mattered more than you expected?", "Review the base and readiness against the actual supported assembly plan."),
        ("The frame begins to rise", "What did the first assembled stage reveal?", "Record the stage, supports, personnel, weather, and measured reference checks."),
        ("Approaching closure", "Where did the last relationships agree or disagree?", "Document fit and corrections; proceed only through the actual assembly plan."),
        ("The honest finish line", "What can you now claim, and what remains to be done?", "Record the achieved condition, actual totals, remaining work, and final photographs."),
    ]
    journal = []
    for day, (title, question, planned) in enumerate(topics, 1):
        p = new_page(f"Day {day:02d} — {title}", "journal", "story",
            f"## Planned focus\n\n{planned}\n\nThis is a proposed focus, not a claim that the work occurred on this day. Record the actual sequence below.\n\n"
            "## Field facts\n\nDate: [record]\n\nStart / finish / breaks: [record]\n\nPeople and labor hours: [record]\n\nWeather and site conditions: [record]\n\n"
            "Starting inventory → accepted output → rejected / reworked → remaining: [record]\n\nMeasurements and configuration used: [record]\n\n"
            f"## The scene\n\n{question}\n\n[Write the actual scene in your own words: what you saw, tried, changed, and understood.]\n\n"
            "## Evidence and next step\n\nPhoto or video IDs, captions, receipts, and notes: [record]\n\nWhat changed in the plan and why: [record]\n\nNext step: [record]\n")
        p["id"] = f"codex-day-{day:02d}"
        p["status"] = "field record needed"
        journal.append(p)
    insert_at = next(i + 1 for i, p in enumerate(pages) if p["id"] == "codex-fortnight-plan")
    pages[insert_at:insert_at] = journal
    return pages


class ConflictError(RuntimeError):
    pass


class BookStore:
    def __init__(self, home=DEFAULT_HOME):
        self.home = Path(home).resolve()
        self.home.mkdir(parents=True, exist_ok=True)
        self.path = self.home / "project.json"
        self.digest = None
        if self.path.exists():
            raw = self.path.read_bytes()
            self.book = json.loads(raw)
            self.digest = hashlib.sha256(raw).hexdigest()
            self.validate(self.book)
        else:
            self.book = dict(schema=SCHEMA, title=TITLE, author="", edition="Codex parallel draft",
                             pages=seed_pages(), assets={}, created=stamp())
            self.save()

    @staticmethod
    def validate(book):
        if book.get("schema") != SCHEMA or not isinstance(book.get("pages"), list):
            raise ValueError(f"Expected a {SCHEMA} book bundle.")
        if not book["pages"]:
            raise ValueError("A book must contain at least one page.")
        seen = set()
        for p in book["pages"]:
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", p.get("id", "")) or p["id"] in seen:
                raise ValueError("Page IDs must be unique, safe identifiers.")
            seen.add(p["id"])
            for key in ("title", "body", "kind", "strand", "status", "notes"):
                if not isinstance(p.get(key), str):
                    raise ValueError(f"Page {p['id']} has invalid {key}.")
            if not isinstance(p.get("figures"), list) or any(not isinstance(x, str) for x in p["figures"]):
                raise ValueError("Figure references must be a list of asset IDs.")
        if not isinstance(book.get("assets", {}), dict):
            raise ValueError("Assets must be an object.")

    def asset_path(self, record):
        path = (self.home / record["path"]).resolve()
        if self.home not in path.parents:
            raise ValueError("Asset path leaves this book workspace.")
        return path

    def save(self):
        self.validate(self.book)
        # Lock and compare are both needed: two editors must not silently win a race.
        lock = self.home / ".save.lock"
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise ConflictError("Another save is in progress. Export your bundle before reopening if this persists.") from None
        try:
            os.close(fd)
            current = hashlib.sha256(self.path.read_bytes()).hexdigest() if self.path.exists() else None
            if current != self.digest:
                raise ConflictError("The book changed in another editor. Your edits remain in memory; export a bundle, then reopen and import it.")
            self.book["updated"] = stamp()
            raw = json.dumps(self.book, indent=2, ensure_ascii=False).encode("utf-8")
            history = self.home / "history"
            history.mkdir(exist_ok=True)
            snapshot = history / (stamp() + "-" + uuid.uuid4().hex[:8] + ".json")
            with snapshot.open("xb") as stream:
                stream.write(raw)
            temporary = self.home / (".save-" + uuid.uuid4().hex + ".tmp")
            temporary.write_bytes(raw)
            os.replace(temporary, self.path)
            self.digest = hashlib.sha256(raw).hexdigest()
            # JSON is authoritative; individual Markdown pages are convenient mirrors.
            folder = self.home / "pages"
            folder.mkdir(exist_ok=True)
            for p in self.book["pages"]:
                target = folder / (p["id"] + ".md")
                content = f"# {p['title']}\n\n{p['body']}"
                if not target.exists() or target.read_text(encoding="utf-8") != content:
                    temp = target.with_suffix(".tmp")
                    temp.write_text(content, encoding="utf-8")
                    os.replace(temp, target)
        finally:
            lock.unlink(missing_ok=True)

    def add_asset(self, source, caption="", provenance="Author-supplied image"):
        from PIL import Image
        source = Path(source)
        with Image.open(source) as im:
            im.verify()
        asset_id = new_id()
        folder = self.home / "assets"
        folder.mkdir(exist_ok=True)
        suffix = source.suffix.lower()
        if suffix not in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
            raise ValueError("Use PNG, JPEG, WebP, or GIF imagery.")
        target = folder / (asset_id + suffix)
        with target.open("xb") as stream:
            stream.write(source.read_bytes())
        self.book["assets"][asset_id] = dict(path=target.relative_to(self.home).as_posix(),
                                             caption=caption, provenance=provenance)
        return asset_id

    def export_bundle(self):
        book = deepcopy(self.book)
        for asset in book["assets"].values():
            asset["data_base64"] = base64.b64encode(self.asset_path(asset).read_bytes()).decode("ascii")
        return self.write_export("book-bundle", ".json", json.dumps(book, indent=2, ensure_ascii=False))

    def import_bundle(self, path):
        book = json.loads(Path(path).read_text(encoding="utf-8"))
        self.validate(book)
        # Validate all content before modifying the live book. Imported pages always
        # receive fresh IDs; origin_id preserves a later human/AI merge relationship.
        assets = {}
        for key, asset in book.get("assets", {}).items():
            if "data_base64" not in asset:
                raise ValueError("Import requires a portable bundle with embedded images.")
            data = base64.b64decode(asset["data_base64"], validate=True)
            from io import BytesIO
            from PIL import Image
            with Image.open(BytesIO(data)) as im:
                image_format = im.format
                im.verify()
            suffix = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp", "GIF": ".gif"}.get(image_format)
            if not suffix:
                raise ValueError("Unsupported embedded image.")
            assets[key] = (data, suffix, asset)
        for p in book["pages"]:
            if any(f not in assets for f in p["figures"]):
                raise ValueError("Bundle references an image it does not contain.")
        mapping = {}
        page_mapping = {p['id']: new_id() for p in book['pages']}
        folder = self.home / "assets"
        folder.mkdir(exist_ok=True)
        for old, (data, suffix, asset) in assets.items():
            fresh = new_id()
            target = folder / (fresh + suffix)
            with target.open("xb") as stream:
                stream.write(data)
            imported_asset = deepcopy(asset)
            imported_asset.pop('data_base64', None)
            imported_asset.update(path=target.relative_to(self.home).as_posix(),
                caption=str(asset.get("caption", "")), provenance=str(asset.get("provenance", "Imported")))
            if imported_asset.get('source_page_id') in page_mapping:
                imported_asset['origin_page_id'] = imported_asset['source_page_id']
                imported_asset['source_page_id'] = page_mapping[imported_asset['source_page_id']]
            self.book["assets"][fresh] = imported_asset
            mapping[old] = fresh
        for p in book["pages"]:
            p = deepcopy(p)
            p["origin_id"] = p["id"]
            p["id"] = page_mapping[p['id']]
            p["figures"] = [mapping[f] for f in p["figures"]]
            p["notes"] = "Imported for review; existing pages preserved.\n" + p["notes"]
            self.book["pages"].append(p)
        return len(book["pages"])

    def write_export(self, name, suffix, content):
        folder = self.home / "exports"
        folder.mkdir(exist_ok=True)
        target = folder / f"{name}-{stamp()}-{uuid.uuid4().hex[:6]}{suffix}"
        with target.open("x", encoding="utf-8") as stream:
            stream.write(content)
        return target

    def set_figure_placement(self, page_id, asset_id, after_paragraph):
        """Set one chapter's figure position without moving a shared image elsewhere.

        Shared image records receive an independent metadata copy; both records
        keep the same existing image file. Returns the chapter's resulting ID.
        """
        from .placement import prose_paragraph_count
        page = next((p for p in self.book["pages"] if p["id"] == page_id), None)
        if page is None or asset_id not in page["figures"] or asset_id not in self.book["assets"]:
            raise ValueError("Attach the image to this chapter before placing it.")
        count = prose_paragraph_count(page["body"])
        if after_paragraph is not None and (isinstance(after_paragraph, bool) or
                not isinstance(after_paragraph, int) or not 0 <= after_paragraph <= count):
            raise ValueError("Choose a position within the chapter's current prose paragraphs.")
        asset = self.book["assets"][asset_id]
        placement = deepcopy(asset.get("book_placement"))
        placement = placement if isinstance(placement, dict) else {}
        if after_paragraph is None:
            placement.pop("after_paragraph", None)
        else:
            placement["after_paragraph"] = after_paragraph
        replacement = deepcopy(asset)
        if placement:
            replacement["book_placement"] = placement
        else:
            replacement.pop("book_placement", None)
        if replacement == asset:
            return asset_id
        shared = any(p["id"] != page_id and asset_id in p["figures"] for p in self.book["pages"])
        if shared:
            fresh = new_id()
            replacement["origin_asset_id"] = asset_id
            self.book["assets"][fresh] = replacement
            page["figures"] = [fresh if key == asset_id else key for key in page["figures"]]
            return fresh
        self.book["assets"][asset_id] = replacement
        return asset_id

    def export_markdown(self):
        from .reading import reading_parts
        text = [f"# {self.book['title']}\n", "## Contents\n"]
        for i, p in enumerate(self.book["pages"], 1):
            text.append(f"{i}. {p['title']} ({p['kind']}; {p['status']})")
        for p in self.book["pages"]:
            text.append(f"\n---\n\n<!-- page-id: {p['id']} -->\n# {p['title']}\n")
            for kind,key in reading_parts(p,self.book['assets']):
                if kind=='text':
                    text.append(key)
                    continue
                asset = self.book["assets"].get(key)
                if asset:
                    text.append(f"\n![{asset['caption']}](../{asset['path']})\n\n{asset['provenance']}\n")
        return self.write_export("manuscript", ".md", "\n".join(text))

    def export_html(self, pages=None):
        from .reading import reading_parts
        pages = pages or self.book["pages"]
        out = ["<!doctype html><html lang='en'><meta charset='utf-8'>",
               "<meta name='viewport' content='width=device-width,initial-scale=1'>",
               f"<title>{html.escape(self.book['title'])}</title>",
               "<style>body{margin:0;background:#e8e4da;color:#283e34;font:18px/1.65 Georgia,serif}"
               "main{max-width:780px;margin:auto}article,nav{background:#fffdf5;padding:65px 75px;margin:24px 0}"
               "h1{font-size:2.3em;line-height:1.15}h2{margin-top:2em}small,.meta,figcaption{font:13px/1.5 system-ui;color:#616f65}"
               "a{color:#416b58}figure{margin:28px 0}img{max-width:100%;max-height:820px;object-fit:contain}"
               "pre{white-space:pre-wrap;font:14px/1.5 Consolas,monospace;background:#eeeee4;padding:18px}"
               "table{border-collapse:collapse;width:100%;font-size:15px}td,th{padding:8px;border-bottom:1px solid #ccc;text-align:left}"
               "blockquote{border-left:3px solid #b88a4f;padding-left:20px}"
               ".part{min-height:600px;display:flex;flex-direction:column;justify-content:center;background:#203f34;color:#fffdf5}"
               "@media(max-width:700px){article,nav{padding:28px 24px;margin:10px}}"
               "@media print{@page{size:6in 9in;margin:0.65in}body{background:white;font-size:11pt}"
               "article,nav{padding:0;margin:0;break-before:page}h1,h2,h3{break-after:avoid}figure{break-inside:avoid}"
               "img{max-height:6in}.part{min-height:6in;background:white;color:#203f34}.screen{display:none}}</style><main>",
               f"<nav><h1>{html.escape(self.book['title'])}</h1><p class='meta'>Working manuscript · {html.escape(self.book.get('edition', ''))}</p>",
               "<p class='screen'>Use your browser’s Print command to print or save as PDF.</p><ol>"]
        for p in pages:
            out.append(f"<li><a href='#{p['id']}'>{html.escape(p['title'])}</a></li>")
        out.append("</ol></nav>")
        for p in pages:
            out.append(f"<article id='{p['id']}' class='{'part' if p['kind'] == 'part' else 'page'}'>"
                       f"<p class='meta'>{html.escape(p['kind'])} · {html.escape(p['strand'])} · {html.escape(p['status'])}</p>"
                       f"<h1>{html.escape(p['title'])}</h1>")
            for kind,key in reading_parts(p,self.book['assets']):
                if kind=='text':
                    out.append(markdown_html(key))
                    continue
                asset = self.book["assets"].get(key)
                if asset:
                    ext = self.asset_path(asset).suffix.lower()
                    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}.get(ext, "image/png")
                    data = base64.b64encode(self.asset_path(asset).read_bytes()).decode("ascii")
                    out.append(f"<figure><img alt='{html.escape(asset['caption'], quote=True)}' src='data:{mime};base64,{data}'>"
                               f"<figcaption>{html.escape(asset['caption'])}<br>{html.escape(asset['provenance'])}</figcaption></figure>")
            out.append("</article>")
        out.append("</main></html>")
        return self.write_export("reading-edition", ".html", "\n".join(out))


def inline(text):
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    # Only external http(s) links; never run raw HTML from an imported manuscript.
    return re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r'<a href="\2">\1</a>', text)


def markdown_html(text):
    """Small safe Markdown subset: headings, paragraphs, lists, tables and code."""
    out, paragraph, table, code = [], [], [], None
    def flush():
        if paragraph:
            out.append("<p>" + inline(" ".join(paragraph)) + "</p>")
            paragraph.clear()
        if table:
            out.append("<table>")
            for i, row in enumerate(table):
                if all(re.fullmatch(r"[: -]+", cell) for cell in row):
                    continue
                tag = "th" if i == 0 else "td"
                out.append("<tr>" + "".join(f"<{tag}>{inline(cell)}</{tag}>" for cell in row) + "</tr>")
            out.append("</table>")
            table.clear()
    for line in text.splitlines():
        if line.startswith("```"):
            flush()
            if code is None:
                code = []
            else:
                out.append("<pre>" + html.escape("\n".join(code)) + "</pre>")
                code = None
        elif code is not None:
            code.append(line)
        elif line.startswith("|"):
            if paragraph:
                flush()
            table.append([cell.strip() for cell in line.strip("|").split("|")])
        elif not line.strip():
            flush()
        elif line.startswith("#"):
            flush()
            level = min(6, len(line) - len(line.lstrip("#")) + 1)
            out.append(f"<h{level}>{inline(line.lstrip('# '))}</h{level}>")
        elif line.startswith("> "):
            flush()
            out.append("<blockquote>" + inline(line[2:]) + "</blockquote>")
        elif re.match(r"(?:[-*] |\d+\. )", line):
            flush()
            out.append("<p>" + inline(line) + "</p>")
        else:
            if table:
                flush()
            paragraph.append(line)
    flush()
    if code is not None:
        out.append("<pre>" + html.escape("\n".join(code)) + "</pre>")
    return "\n".join(out)

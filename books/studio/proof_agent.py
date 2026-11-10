"""The Proof Desk's DeepSeek agent: it reads the printed pages, finds their source, and proposes fixes.

It sees what the owner sees -- the page open on the desk, its words, its measured margins and the
preflight -- and works through the desk's own functions (books.studio.proof) and the manuscript's
(books.studio.manuscripts). It never changes the book by itself: an edit comes back as a proposal
(chapter, exact passage, replacement, why) the owner applies or discards, and a note it pins is
marked as the agent's. New writing follows the same path, as a proposed insertion after an exact
passage. Numbers stay {{tokens}}, as in the rest of the studio.
"""

from __future__ import annotations

import json

from books.studio import agent as A
from books.studio import manuscripts as MS
from books.studio import proof as P

MAX_STEPS = 18

RULES = """You are the proofreader and editor at the Proof Desk of a geodesic-dome project's books.
The owner is checking the finished print PDF of a book before uploading it to Amazon KDP.
Pages are the printed PDF's pages, numbered from 1. The words on them come from Markdown chapters; every fix goes into a chapter, never into the PDF.
Work only through the tools. Read before you write: read the page, find where its words come from, read that part of the chapter.
To change words, call propose_edit with a passage copied exactly from the chapter (enough of it to be unique) and its replacement.
To add new writing, call propose_edit with the passage it should follow as `find` and that passage plus the new text as `replace`.
The owner applies each proposal; say so, and do not claim the book has changed.
Never type a dimension, count, price or weight the book's numbers can supply: keep every {{token}} exactly as it is, and never invent a figure.
Keep the book's voice: plain, exact, first-hand. Prefer small edits.
Pin a note (add_note) for anything you find that is not a wording fix -- layout, a picture, a margin -- or that the owner must decide.
When you are done, answer in a few plain sentences: what you found, what you proposed, what is left."""

S, I, N = {"type": "string"}, {"type": "integer"}, {"type": "number"}

TOOLS = [
    A._tool("read_page", "A printed page: its words, measured margins (inches), pictures with their ppi, and the chapter its words come from.",
            {"page": I}, ["page"]),
    A._tool("search_book", "The printed pages a phrase appears on.", {"text": S}, ["text"]),
    A._tool("find_in_manuscript", "Where a phrase appears in the Markdown chapters: chapter path, line, and the line itself.",
            {"text": S}, ["text"]),
    A._tool("list_chapters", "The book's chapters (path, title, words).", {}, []),
    A._tool("read_chapter", "A chapter's Markdown, with line numbers; give `from_line` and `lines` to read part of a long one.",
            {"path": S, "from_line": I, "lines": I}, ["path"]),
    A._tool("propose_edit", "Propose replacing an exact passage of a chapter (or inserting after one). The owner reviews and applies it.",
            {"path": S, "find": S, "replace": S, "why": S, "page": I}, ["path", "find", "replace", "why"]),
    A._tool("preflight", "The KDP preflight of this build: every check, pass, warn or fail, with the pages each concerns.", {}, []),
    A._tool("list_notes", "The proof notes on this build (open and resolved).", {}, []),
    A._tool("add_note", "Pin a note to a page: kind is fix, question, ok or note. `rect` is [x0,y0,x1,y1] in PDF points if it is about one spot.",
            {"page": I, "text": S, "kind": S, "rect": {"type": "array", "items": N}}, ["page", "text"]),
    A._tool("resolve_note", "Mark a note resolved, with a reply saying why.", {"id": S, "reply": S}, ["id"]),
]


def _numbered(text: str, start: int = 1, count: int | None = None) -> str:
    lines = text.splitlines()
    start = max(1, start)
    end = len(lines) if count is None else min(len(lines), start - 1 + count)
    return "\n".join(f"{i:>4}  {lines[i - 1]}" for i in range(start, end + 1)) + (f"\n... ({len(lines)} lines in all)" if end < len(lines) else "")


def find_in_manuscript(key: str, text: str, limit: int = 20) -> list[dict]:
    want = P._norm(text)
    if len(want) < 3:
        return []
    out = []
    for path, raw, _ in P.sources(key):
        for i, ln in enumerate(raw.splitlines(), start=1):
            if want in P._norm(ln):
                out.append({"path": path, "line": i, "text": ln[:400]})
                if len(out) >= limit:
                    return out
    return out


def run(key: str, build: str, page: int, message: str, history: list | None = None, llm=A._llm) -> dict:
    """One request, worked through to the end. Returns the reply, the tool calls made, the edits
    proposed and the notes pinned."""
    b = MS.book(key)
    here = P.page(key, build, page)
    src = P.source_for(key, here["text"])
    context = (f"The book: {b.title}. The build on the desk: {build}, {here['pages']} pages.\n"
               f"The owner is looking at page {page}" + (f", whose words come from {src['path']} near line {src['line']}." if src else ".")
               + f"\nIts margins (inches): {json.dumps(here['margins'])}; inside edge on the {here['inside']}.")
    messages = [{"role": "system", "content": RULES + "\n\n" + context}, *(history or [])[-10:], {"role": "user", "content": message}]
    calls, proposals, pinned = [], [], []

    for _ in range(MAX_STEPS):
        msg = llm(messages, TOOLS)
        messages.append({k: v for k, v in msg.items() if k in ("role", "content", "tool_calls")})
        if not msg.get("tool_calls"):
            return {"reply": msg.get("content") or "", "calls": calls, "proposals": proposals, "notes": pinned}
        for tc in msg["tool_calls"]:
            name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            try:
                if name == "read_page":
                    pg = P.page(key, build, int(args["page"]))
                    result = {k: pg[k] for k in ("n", "pages", "text", "margins", "inside", "blank")}
                    result["pictures"] = pg["images"]
                    result["source"] = P.source_for(key, pg["text"])
                elif name == "search_book":
                    result = [{"page": x["n"], "times": len(x["hits"])} for x in P.search(key, build, args["text"], limit=40)]
                elif name == "find_in_manuscript":
                    result = find_in_manuscript(key, args["text"])
                elif name == "list_chapters":
                    result = [{k: c[k] for k in ("path", "title", "words")} for c in MS.chapters(key)]
                elif name == "read_chapter":
                    text = MS.read(key, args["path"])
                    result = _numbered(text, int(args.get("from_line") or 1), int(args["lines"]) if args.get("lines") else None)[:24000]
                elif name == "propose_edit":
                    text = MS.read(key, args["path"])
                    count = text.count(args["find"])
                    if not count:
                        raise ValueError("that passage is not in the chapter, word for word; read the chapter and copy it exactly")
                    if count > 1:
                        raise ValueError(f"that passage is in the chapter {count} times; include more of it so it is unique")
                    proposals.append({**{k: args.get(k, "") for k in ("path", "find", "replace", "why")}, "page": args.get("page") or page})
                    result = "proposed; the owner will review it"
                elif name == "preflight":
                    pf = P.preflight(key, build)
                    result = {"pages": pf["pages"], "fails": pf["fails"], "warns": pf["warns"],
                              "checks": [{k: c[k] for k in ("title", "status", "detail", "pages")} for c in pf["checks"]]}
                elif name == "list_notes":
                    result = [{k: x.get(k) for k in ("id", "here", "kind", "status", "text", "author")} for x in P.notes_for(key, build)]
                elif name == "add_note":
                    got = P.add_note(key, build, int(args["page"]), args["text"], args.get("kind") or "note", args.get("rect"), author="agent")
                    pinned.append(got)
                    result = {"id": got["id"]}
                elif name == "resolve_note":
                    result = P.update_note(key, args["id"], status="resolved", reply=args.get("reply"), author="agent")["status"]
                else:
                    raise ValueError(f"no tool {name}")
                calls.append({"name": name, "args": args, "ok": True})
            except Exception as e:                   # the agent hears the error and can try again
                result = f"error: {e}"
                calls.append({"name": name, "args": args, "ok": False, "error": str(e)})
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": json.dumps(result, ensure_ascii=False)[:24000]})
    return {"reply": "I stopped after the step limit; here is what I did so far.", "calls": calls, "proposals": proposals, "notes": pinned}

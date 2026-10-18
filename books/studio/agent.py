"""The Book Studio's DeepSeek agent: it reads a book and changes it through the studio's own tools.

For a layout book it works on a copy of the open document with the same operations the page uses
(doc.OPS), can look through the picture library and draw new illustrations (library.deepseek_svg),
and hands back the changed document. The studio puts that on its undo stack and nothing is saved
until the owner saves. For a manuscript book it reads chapters and *proposes* replacements; the
owner applies each one. Numbers stay {{tokens}}: the agent is told never to type a figure the
book's token table can fill.
"""

from __future__ import annotations

import copy
import json
import urllib.request

from books.studio import doc as D
from books.studio import library as lib
from books.studio import manuscripts as MS

MAX_STEPS = 18

RULES = """You are the Book Studio's layout and editing assistant for the books of a geodesic-dome project.
Work only through the tools. Pages are numbered from 1; frames and pages also have ids like p1a2b3c4 / f1a2b3c4.
Frames are placed in inches from the page's top-left corner; keep them inside the page.
Text frames hold plain text: a blank line between paragraphs, **bold**, *italic*.
Never type a dimension, count, price or weight the book's numbers can supply: keep any {{token}} you find exactly as it is.
Keep the book's voice and house style. Prefer small, exact edits; read before you write.
When you are done, answer in two or three plain sentences saying what you changed."""


def _tool(name: str, desc: str, props: dict, required: list[str]) -> dict:
    return {"type": "function", "function": {"name": name, "description": desc,
                                             "parameters": {"type": "object", "properties": props, "required": required}}}


NUM, STR, INT, BOOL = {"type": "number"}, {"type": "string"}, {"type": "integer"}, {"type": "boolean"}
FRAME_PROPS = {"x": NUM, "y": NUM, "w": NUM, "h": NUM, "rot": NUM, "text": STR, "style": STR, "src": STR, "fit": STR,
               "fill": STR, "stroke": STR, "strokeW": NUM, "opacity": NUM, "shape": STR, "name": STR}

LAYOUT_TOOLS = [
    _tool("outline", "The whole book: its pages, frames (ids, boxes, text) and styles.", {}, []),
    _tool("add_page", "Add a page after page number `after` (0 for the front), optionally copying page `copy_of`.",
          {"after": INT, "name": STR, "copy_of": STR}, []),
    _tool("delete_page", "Delete a page (number or id).", {"page": STR}, ["page"]),
    _tool("move_page", "Move a page to position `to`.", {"page": STR, "to": INT}, ["page", "to"]),
    _tool("rename_page", "Name a page.", {"page": STR, "name": STR}, ["page", "name"]),
    _tool("add_frame", "Add a text, image or shape frame to a page.", {"page": STR, "kind": STR, **FRAME_PROPS}, ["page", "kind", "x", "y", "w", "h"]),
    _tool("update_frame", "Change a frame's box, text, style, picture or colours.", {"frame": STR, **FRAME_PROPS}, ["frame"]),
    _tool("delete_frame", "Remove a frame.", {"frame": STR}, ["frame"]),
    _tool("arrange", "Bring a frame to the front, send it to the back, forward or backward.", {"frame": STR, "to": STR}, ["frame", "to"]),
    _tool("set_style", "Create or change a named text style.", {"name": STR, "font": STR, "size": NUM, "leading": NUM, "colour": STR,
                                                              "align": STR, "weight": INT, "italic": BOOL}, ["name"]),
    _tool("set_page_size", "Change the trim (inches), margin or paper colour.", {"w": NUM, "h": NUM, "margin": NUM, "paper": STR}, []),
    _tool("find_replace", "Replace text in every text frame.", {"find": STR, "replace": STR, "regex": BOOL}, ["find", "replace"]),
    _tool("set_title", "Rename the book.", {"title": STR}, ["title"]),
    _tool("list_library", "Find pictures in the library by words in their names. Returns names and files (the `src` for an image frame).",
          {"text": STR}, []),
    _tool("make_illustration", "Draw a new illustration from a description (DeepSeek, as SVG, in the house style) and file it. "
                               "Returns its file, to use as an image frame's `src`.",
          {"name": STR, "description": STR, "w": NUM, "h": NUM}, ["name", "description"]),
]

MANUSCRIPT_TOOLS = [
    _tool("list_chapters", "The book's Markdown chapters.", {}, []),
    _tool("read_chapter", "Read one chapter.", {"path": STR}, ["path"]),
    _tool("propose_replace", "Propose replacing an exact passage in a chapter. The owner reviews and applies it.",
          {"path": STR, "find": STR, "replace": STR, "why": STR}, ["path", "find", "replace"]),
]


def _llm(messages: list, tools: list) -> dict:
    from project_agent import config
    if not config.llm_configured():
        raise RuntimeError("no DeepSeek key: set DEEPSEEK_API_KEY")
    body = {"model": config.llm_model(), "messages": messages, "tools": tools, "temperature": 0.3}
    req = urllib.request.Request(config.llm_api_base() + "/chat/completions", data=json.dumps(body).encode("utf-8"),
                                 headers={"Authorization": f"Bearer {config.llm_api_key()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=config.llm_timeout()) as r:
        return json.loads(r.read().decode("utf-8"))["choices"][0]["message"]


def run(instruction: str, *, layout: dict | None = None, book_key: str | None = None, page: int | None = None,
        selected: list[str] | None = None, history: list | None = None, llm=_llm) -> dict:
    """One instruction, worked through to the end. Returns the reply, the changed document (layout
    books), every tool call made, proposals (manuscript books) and illustrations drawn."""
    work = copy.deepcopy(layout) if layout is not None else None
    calls, proposals, drawn = [], [], []
    if work is not None:
        context = f"The open layout book:\n{D.outline(work)}"
        if page:
            context += f"\nThe owner is looking at page {page}."
        if selected:
            context += f"\nSelected frames: {', '.join(selected)}."
        tools = LAYOUT_TOOLS
    else:
        b = MS.book(book_key or "")
        context = (f"The open manuscript book: {b.title} (built by {b.engine}). Its chapters:\n"
                   + "\n".join(f"- {c['path']}: {c['title']} ({c['words']} words)" for c in MS.chapters(b.key)[:200]))
        tools = MANUSCRIPT_TOOLS
    messages = [{"role": "system", "content": RULES + "\n\n" + context}, *(history or [])[-8:], {"role": "user", "content": instruction}]

    for _ in range(MAX_STEPS):
        msg = llm(messages, tools)
        messages.append({k: v for k, v in msg.items() if k in ("role", "content", "tool_calls")})
        if not msg.get("tool_calls"):
            return {"reply": msg.get("content") or "", "doc": work, "calls": calls, "proposals": proposals, "drawn": drawn,
                    "changed": any(c["ok"] and c["name"] not in ("outline", "list_library") for c in calls)}
        for tc in msg["tool_calls"]:
            name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            try:
                if name == "outline":
                    result = D.outline(work)
                elif name == "list_library":
                    result = [{"name": e["name"], "src": e["file"], "category": e["category"]} for e in lib.entries(args.get("text", ""))[:40]]
                elif name == "make_illustration":
                    svg = lib.deepseek_svg(args["description"], float(args.get("w", 1) or 1), float(args.get("h", 1) or 1))
                    got = lib.add_svg(args["name"], svg, "deepseek", args["description"], "Drawn by DeepSeek in the Book Studio.")
                    drawn.append(got)
                    result = {"src": got["file"]}
                elif name == "list_chapters":
                    result = MS.chapters(book_key)
                elif name == "read_chapter":
                    result = MS.read(book_key, args["path"])[:24000]
                elif name == "propose_replace":
                    text = MS.read(book_key, args["path"])
                    if args["find"] not in text:
                        raise ValueError("that passage is not in the chapter, word for word")
                    proposals.append({k: args.get(k, "") for k in ("path", "find", "replace", "why")})
                    result = "proposed; the owner will review it"
                else:
                    result = D.apply(work, name, args)
                calls.append({"name": name, "args": args, "ok": True})
            except Exception as e:                   # the agent hears the error and can try again
                result = f"error: {e}"
                calls.append({"name": name, "args": args, "ok": False, "error": str(e)})
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": json.dumps(result, ensure_ascii=False)[:24000]})
    return {"reply": "I stopped after the step limit; here is what I did so far.", "doc": work, "calls": calls,
            "proposals": proposals, "drawn": drawn, "changed": bool(calls)}

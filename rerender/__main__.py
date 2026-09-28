"""Command line for the Cabin World re-render queue.

    py -3.12 -m rerender list [--status todo]      every film and where it stands
    py -3.12 -m rerender show KEY                  one film's catalogue entry
    py -3.12 -m rerender prompt KEY [--no-save]    the copy-prompt blueprint
    py -3.12 -m rerender prompt --queue            "take the next film" blueprint
    py -3.12 -m rerender next                      the next open item
    py -3.12 -m rerender claim KEY --by NAME [--force]
    py -3.12 -m rerender status KEY STATUS --by NAME [--output PATH ...] [--text "..."]
    py -3.12 -m rerender note KEY "text" --by NAME
    py -3.12 -m rerender priority KEY high|normal|low
    py -3.12 -m rerender stills KEY [--size 1080x1920]   one still per chapter, to look at
    py -3.12 -m rerender render KEY [--out PATH]         THE render: landscape, phone, release
      (KEY is a queue item, or any lesson key, e.g. cabin_pilot)
    py -3.12 -m rerender refresh                   re-read every film from the code (slow)
    py -3.12 -m rerender export                    write every blueprint to rerender/prompts/
    py -3.12 -m rerender check                     validate the catalogue, queue and prompts
"""

from __future__ import annotations

import argparse
import json
import sys

from . import blueprint, catalogue, state


def _item(key: str):
    table = catalogue.by_key()
    if key not in table:
        raise SystemExit(f"no queue item {key!r}; `py -3.12 -m rerender list` shows them")
    return table[key]


def cmd_list(args) -> int:
    items = catalogue.load()
    data = state.load()
    for i in items:
        e = state.entry(data, i)
        if args.status and e["status"] != args.status:
            continue
        who = f" [{e['owner']}]" if e["owner"] else ""
        print(f"{e['status']:<9} {e['priority']:<6} {i.key:<34} {len(i.chapters):>3} ch  "
              f"{i.title}{who}")
    return 0


def _lesson_and_file(key: str, out: str = "") -> tuple[str, str]:
    """A queue item's re-render, or any lesson by its own key."""
    table = catalogue.by_key()
    if key in table:
        item = table[key]
        return item.target_key, out or item.target_file
    from two_v_demo.deliverables import DELIVERABLE_BY_LESSON, OUTPUT_DIR
    from two_v_demo.lesson_registry import LESSONS

    if key not in LESSONS:
        raise SystemExit(f"{key!r} is neither a queue item nor a lesson key")
    d = DELIVERABLE_BY_LESSON.get(key)
    name = d.filename if d else f"{catalogue.slug(LESSONS[key].title)}.mp4"
    return key, out or (OUTPUT_DIR / name).as_posix()


def _run_masterclass(ticket: dict) -> int:
    import subprocess

    import launcher_common as lc

    lc.write_config("two_v_masterclass", ticket)
    return subprocess.run([sys.executable, "two_v_masterclass.py"],
                          cwd=str(catalogue.ROOT)).returncode


def cmd_stills(args) -> int:
    """One still per chapter, 70% of the way in, where the chapter has built up."""
    from two_v_demo.lesson_registry import LESSONS

    lesson_key, _file = _lesson_and_file(args.key)
    if lesson_key not in LESSONS:
        raise SystemExit(f"lesson {lesson_key!r} is not written yet -- make its module first")
    times, cursor = [], 0.0
    for ch in LESSONS[lesson_key].chapters:
        times.append(round(cursor + ch.duration * 0.7, 2))
        cursor += ch.duration
    print(f"stills of {lesson_key} at {args.size}: two_v_demo_output/{lesson_key}/")
    return _run_masterclass({"lesson": lesson_key, "action": "shots", "size": args.size,
                             "shots": ",".join(str(t) for t in times)})


def cmd_render(args) -> int:
    """The finished film: landscape, phone cut and release folder."""
    from two_v_demo.lesson_registry import LESSONS

    lesson_key, target = _lesson_and_file(args.key, args.out)
    if lesson_key not in LESSONS:
        raise SystemExit(f"lesson {lesson_key!r} is not written yet -- make its module first")
    print(f"rendering {lesson_key} -> {target} (and its phone cut and release folder); "
          "this takes one to two hours")
    return _run_masterclass({"action": "export_video", "lesson": lesson_key,
                             "export_video": target, "size": "1920x1080", "fps": 30,
                             "compose_segments": not args.no_segments})


def check() -> None:
    items = catalogue.load()
    keys = [i.key for i in items]
    assert len(keys) == len(set(keys)), "duplicate keys"
    targets = [i.target_key for i in items]
    assert len(targets) == len(set(targets)), "two items would write the same lesson"
    for i in items:
        assert i.chapters, f"{i.key} has no chapters"
        assert i.source and (catalogue.ROOT / i.source).is_file(), f"{i.key}: source missing"
        for o in i.originals:
            assert (catalogue.ROOT / o).is_file(), f"{i.key}: original vanished: {o}"
        assert not (catalogue.ROOT / i.target_module).exists() or \
            state.entry(state.load(), i)["status"] != "todo", \
            f"{i.key}: {i.target_module} exists but the item is still todo"
    data = state.load()
    for key, e in data["items"].items():
        assert key in keys, f"queue has an unknown item {key}"
        assert e.get("status", "todo") in state.STATUSES
    text = blueprint.item_prompt(items[0], items)
    for heading in ("## 1.", "## 2.", "## 3.", "## 4.", "## 8.", "## 9."):
        assert heading in text, heading
    assert "Never overwrite a deliverable" in text, "the rules are not in the prompt"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="rerender", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list"); p.add_argument("--status", choices=state.STATUSES)
    p = sub.add_parser("show"); p.add_argument("key")
    p = sub.add_parser("prompt"); p.add_argument("key", nargs="?")
    p.add_argument("--queue", action="store_true"); p.add_argument("--no-save", action="store_true")
    sub.add_parser("next")
    p = sub.add_parser("claim"); p.add_argument("key"); p.add_argument("--by", required=True)
    p.add_argument("--force", action="store_true")
    p = sub.add_parser("status"); p.add_argument("key"); p.add_argument("status", choices=state.STATUSES)
    p.add_argument("--by", default=""); p.add_argument("--output", nargs="*", default=[])
    p.add_argument("--text", default="")
    p = sub.add_parser("note"); p.add_argument("key"); p.add_argument("text"); p.add_argument("--by", default="")
    p = sub.add_parser("priority"); p.add_argument("key"); p.add_argument("level", choices=state.PRIORITIES)
    p = sub.add_parser("stills"); p.add_argument("key")
    p.add_argument("--size", default="1920x1080")
    p = sub.add_parser("render"); p.add_argument("key"); p.add_argument("--out", default="")
    p.add_argument("--no-segments", action="store_true")
    sub.add_parser("refresh"); sub.add_parser("export"); sub.add_parser("check")
    p = sub.add_parser("json"); p.add_argument("--with-state", action="store_true")
    args = parser.parse_args(argv)

    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    try:
        if args.cmd == "list":
            return cmd_list(args)
        if args.cmd == "show":
            i = _item(args.key)
            print(json.dumps({**catalogue.asdict(i), "state": state.entry(state.load(), i)},
                             indent=1, ensure_ascii=False))
            return 0
        if args.cmd == "prompt":
            if args.queue:
                text, key = blueprint.queue_prompt(), "_queue"
            elif args.key:
                text, key = blueprint.prompt_for(args.key), args.key
            else:
                raise SystemExit("give a KEY or --queue")
            if not args.no_save:
                path = blueprint.save(key, text)
                print(f"<!-- saved to {path} -->", file=sys.stderr)
            print(text)
            return 0
        if args.cmd == "next":
            nxt = state.next_item(catalogue.load())
            print(nxt.key if nxt else "(nothing open)")
            return 0 if nxt else 1
        if args.cmd == "claim":
            e = state.claim(_item(args.key), args.by, args.force)
            print(f"{args.key}: claimed by {e['owner']}")
            return 0
        if args.cmd == "status":
            e = state.set_status(_item(args.key), args.status, args.by, args.output, args.text)
            print(f"{args.key}: {e['status']}")
            return 0
        if args.cmd == "note":
            state.note(_item(args.key), args.by, args.text)
            print(f"{args.key}: noted")
            return 0
        if args.cmd == "priority":
            state.set_priority(_item(args.key), args.level)
            print(f"{args.key}: {args.level}")
            return 0
        if args.cmd == "stills":
            return cmd_stills(args)
        if args.cmd == "render":
            return cmd_render(args)
        if args.cmd == "refresh":
            items = catalogue.refresh()
            print(f"catalogue: {len(items)} films, "
                  f"{sum(len(i.chapters) for i in items)} chapters -> {catalogue.CATALOGUE}")
            return 0
        if args.cmd == "export":
            items = catalogue.load()
            for i in items:
                blueprint.save(i.key, blueprint.item_prompt(i, items))
            blueprint.save("_queue", blueprint.queue_prompt(items))
            print(f"wrote {len(items) + 1} blueprints to {blueprint.PROMPTS}")
            return 0
        if args.cmd == "json":
            items = catalogue.load()
            data = state.load()
            print(json.dumps([{**catalogue.asdict(i), **({"state": state.entry(data, i)}
                                                         if args.with_state else {})}
                              for i in items], ensure_ascii=False))
            return 0
        if args.cmd == "check":
            check()
            print("rerender: catalogue, queue and blueprints check out")
            return 0
    except (PermissionError, RuntimeError, FileNotFoundError, ValueError, KeyError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""The writers' room: a season's outlines turned into episode scripts.

* :func:`skeleton` -- an episode file from its outline: one scene per plot strand, a placeholder
  line for each character the outline names, and the episode's cliffhanger, ready to write into
  in the Director.
* :func:`draft` -- DeepSeek writes the whole episode as beats, from the series bible, the season
  plan, the outline and the pilot as the worked example. The draft is checked against the
  engine's beat kinds, the cast and the sets before it is saved, and it is saved as a draft:
  the previous file, if any, is kept.
* :func:`coverage` -- what the scripted episodes actually contain: lines and talk per character,
  each quirk's appearances (thought spirals, visions, side-eyes, the earring, the foot coming
  down), and the gaps the season plan leaves.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
EPISODES = HERE / "episodes"

KINDS = {"scene", "line", "walk", "act", "face", "cam", "wait", "sfx", "music", "view", "build", "lower", "figure", "card", "gag", "meme",
         "credits", "thought", "vision", "expr", "prop", "mood", "flash", "place"}
SETS = {"studio": "Hank's Hardware Hour bench and table saw, x -7..-3, y -5..1 (bench at -6.2,-2.0; the saw at -6.4,-4.6)",
        "patio": "the back patio, table at 0,8.2, the house wall at y 10.4, Dusty's car on the driveway at -7.4,8.4",
        "yard": "the dome site: the dome at the origin, door facing -y, the porch from y -2.5 to -4.9 (|x| < 1.6)",
        "hedge": "the neighbour's hedge at x 5.6; Mr. Yarrow stands behind it at about 6.1,0.6 facing -x",
        "inside": "inside the finished dome, floor radius about 2.2 m"}
TOKENS = "{bevel} {bevel_spoken} {fold} {fold_spoken} {tail} {panels} {panels_words} {sticks_words} {cuts_words} {sqft} {sqft_words} {ft_words}"


def load(name: str) -> dict:
    return json.loads((EPISODES / f"{name}.json").read_text(encoding="utf-8"))


def save(name: str, data: dict) -> str | None:
    """Write an episodes/ file, keeping the one it replaces in episodes/.versions."""
    f = EPISODES / f"{name}.json"
    kept = None
    if f.exists():
        keep = EPISODES / ".versions"
        keep.mkdir(exist_ok=True)
        kept = keep / f"{name}-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        kept.write_bytes(f.read_bytes())
    f.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    return kept.name if kept else None


def _episode(season: dict, eid: str) -> dict:
    for e in season["episodes"]:
        if e["id"] == eid:
            return e
    raise ValueError(f"{eid} is not in {season['id']}")


# ----------------------------------------------------------------------
# A skeleton from the outline
# ----------------------------------------------------------------------

def skeleton(season_id: str, eid: str) -> dict:
    season, series = load(season_id), load("series")
    e = _episode(season, eid)
    cast = list(series["cast"])
    named = lambda text: [c for c in cast if re.search(rf"\b{series['cast'][c]['name'].split()[0]}\b", text, re.I) or re.search(rf"\b{c}\b", text, re.I)]
    beats = [{"k": "card", "text": series["title"].upper(), "sub": f"Episode {int(eid[-2:])}: {e['title']}", "secs": 4, "music": "theme"}]
    places = {"A": ("yard", "golden"), "B": ("patio", "dusk"), "C": ("studio", "day")}
    spots = [[0.5, -3.9, -20], [-1.4, -4.2, 20], [1.4, -4.6, 40], [-0.4, -4.5, 0], [-1.0, -3.6, 10], [2.2, -4.0, 60]]
    patio = [[1.3, 8.4, 90], [-1.2, 8.2, -90], [-0.6, 7.1, -15], [0.7, 7.1, 20], [0.0, 9.3, 180], [-2.0, 7.6, -60]]
    studio = [[-5.2, -1.3, -90], [-5.2, -2.8, -90], [-3.6, -3.6, 125], [-4.0, -0.4, -120]]
    for strand, text in e.get("plots", {}).items():
        at, mood = places.get(strand, ("yard", "day"))
        who = named(text) or ["hank", "krystal"]
        pool = {"yard": spots, "patio": patio, "studio": studio}[at]
        beats.append({"k": "scene", "name": f"{strand} plot: {text[:60]}", "at": at, "mood": mood,
                      "place": {w: pool[k % len(pool)] for k, w in enumerate(who[:len(pool)])}, "view": {"step": 6 + int(eid[-2:]), "explode": 0}})
        beats.append({"k": "music", "name": "pad", "secs": 12, "mood": "tense" if e.get("tone", {}).get("drama", 0.5) > 0.6 else "warm"})
        for w in who[:4]:
            beats.append({"k": "line", "who": w, "text": f"[{series['cast'][w]['name'].split()[0]}: write this line. {text[:80]}]", "act": "talk",
                          "cam": {"kind": "single", "who": w, "size": "medium"}})
    beats.append({"k": "scene", "name": f"Cliffhanger: {e.get('cliffhanger', '')[:60]}", "at": "yard", "mood": "night",
                  "place": {"cody": [0.3, -3.7, 0]}, "view": {"step": 6 + int(eid[-2:])}})
    beats.append({"k": "line", "who": "cody", "text": f"[the cliffhanger: {e.get('cliffhanger', '')}]", "act": "vision", "expr": "vision"})
    beats.append({"k": "credits", "secs": 6})
    return {"id": eid, "season": season_id, "series": series["title"], "number": e["number"], "title": e["title"], "logline": e["logline"],
            "rating": series.get("rating", "PG-13"), "status": "skeleton", "beats": beats}


# ----------------------------------------------------------------------
# Checking a script against what the engine can play
# ----------------------------------------------------------------------

def check(ep: dict, series: dict) -> list[str]:
    problems = []
    cast = set(series["cast"])

    def walk(beats, where=""):
        for i, b in enumerate(beats):
            at = f"{where}beat {i + 1}"
            k = b.get("k")
            if k not in KINDS:
                problems.append(f"{at}: unknown kind {k!r}")
                continue
            for key in ("who",):
                if key in b and b[key] not in cast:
                    problems.append(f"{at}: {b[key]!r} is not in the cast")
            for w in (b.get("place") or {}):
                if w not in cast:
                    problems.append(f"{at}: {w!r} placed but not in the cast")
            if k == "line" and not (b.get("text") or b.get("frags")):
                problems.append(f"{at}: a line with nothing to say")
            if k == "vision":
                walk(b.get("beats", []), f"{at} > ")
            cam = b.get("cam") or {}
            for key in ("who", "a", "b", "over", "at", "toward"):
                v = cam.get(key)
                if isinstance(v, str) and v not in cast and key != "at":
                    problems.append(f"{at}: the camera's {key} {v!r} is not in the cast")
    walk(ep.get("beats", []))
    return problems


# ----------------------------------------------------------------------
# DeepSeek writes a draft
# ----------------------------------------------------------------------

SCHEMA = """An episode is JSON: {"id","season","series","number","title","logline","rating","status","beats":[...]}.
Beats run in order. Kinds and fields:
- scene: {"k":"scene","name","at":"studio|patio|yard|hedge|inside","mood":"day|golden|dusk|night|overcast|storm","sun":[azimuth,elevation],
          "place":{"who":[x,y,yaw_degrees]},"hide":[who],"view":{"step":int,"explode":0..0.2,"door":0..90,"tagsOff":["furniture","skin","glass"]},"panelOnBench":bool}
- line: {"k":"line","who","text"} or with "frags":[{"text","rate":"+20%","pause":0.3}] for stop-and-go speech; optional "act","after","expr","keepExpr",
        "earring":bool (Jet), "stomp":true (Krystal's foot coming down), "pad":seconds, "listeners":[who],
        "cam": {"kind":"single","who","toward","size":"close|medium|wide","side":1|-1,"lens":mm} | {"kind":"two","a","b","dist"} |
               {"kind":"ots","over","at"} | {"kind":"wide","who":[...],"dir":[x,y,z]} | {"kind":"low","who","dist","lens"} |
               {"kind":"move","move":"dollyIn|dollyOut|orbit|slide|pan|crane|pedestal|dollyZoom|reveal|flyover|spiral|hold","from":[x,y,z],"subject":"who|dome|jig|saw|patio|hedge|[x,y,z]","lens":mm}
- thought: Hank only. {"k":"thought","who":"hank","frags":[{"text","rate","pause","word"}],"ghosts":[acts]}: his permutational inner scene; 4 to 7 fragments.
- vision: Cody only. {"k":"vision","who":"cody","label","beats":[a scene beat and a few cam/wait/flash/music/line beats]}: a flash of what's coming.
- walk {"who","to":[x,y],"speed","wait"}; place {"who","at":[x,y,yaw]}; act {"who","act"}; face {"who","at":who|[x,y]}; expr {"who","expr"};
  prop {"who","prop":"earring|phone","on"}; cam {"cam","dur","wait"}; wait {"s"}; sfx {"name"}; music {"name":"pad|tension|piano|rain|heart|theme","secs","mood":"warm|sad|tense|hope|night|inner"};
  card {"text","sub","secs","music":"theme|sting"}; lower {"who"} (a name caption, the first time someone speaks); figure {"big","small","secs"};
  meme {"style":"freeze|zoom|caption|pov","text","who","secs","sfx":"scratch|boom|airhorn"}; gag {"name":"handPanel|burstPanel|tiltBlade","who"};
  build {"from","to","every"} (the dome going up); flash {"secs","sfx"}; mood {"mood"}; credits {"secs"}.
Acts: idle talk point wave shrug hips think facepalm cheer laugh hammer carry lift crank measure flex grunt peek phone sit fall stomp crossed vision ear lean spiral.
Expressions: neutral sideeye sideeyeL glare wide smile smirk sad vision far.
Figures about the dome are written as tokens, never typed: """ + TOKENS


def draft(season_id: str, eid: str, timeout: float = 300) -> dict:
    from project_agent import config
    if not config.llm_configured():
        raise RuntimeError("no DeepSeek key is set (project_agent config)")
    season, series, pilot = load(season_id), load("series"), load("s01e01")
    e = _episode(season, eid)
    prev = [x for x in season["episodes"] if x["id"] < eid]
    system = ("You are the head writer of a TV series and you write in JSON. You write hyper-drama with a slight comedy: real stakes, "
              "fast turns, jokes between the feelings. Characters stay in character and their quirks show in action, not exposition. "
              "The writers' room themes are undercurrents: no character ever states them. PG-13 language at most. Output only the JSON object.")
    user = json.dumps({
        "series_bible": series, "season_plan": {k: season[k] for k in ("title", "arc", "threads")},
        "earlier_episodes": [{k: x[k] for k in ("number", "title", "logline", "cliffhanger")} for x in prev],
        "write_this_episode": e, "sets": SETS, "schema": SCHEMA,
        "worked_example_pilot": pilot,
        "length": "5 to 8 minutes: about 50 to 80 lines across 6 to 9 scenes, with music beds under quiet scenes so there is no dead air.",
    }, ensure_ascii=False)
    body = {"model": config.llm_model(), "temperature": 0.8, "max_tokens": 8000, "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    req = urllib.request.Request(config.llm_api_base() + "/chat/completions", data=json.dumps(body).encode("utf-8"),
                                 headers={"Authorization": f"Bearer {config.llm_api_key()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        reply = json.loads(r.read().decode("utf-8"))["choices"][0]["message"]["content"]
    m = re.search(r"\{.*\}", reply, re.S)
    ep = json.loads(m.group(0) if m else reply)
    ep.update({"id": eid, "season": season_id, "series": series["title"], "number": e["number"], "title": e["title"], "status": "draft",
               "drafted_by": "deepseek"})
    problems = check(ep, series)
    if problems:
        # keep only what the engine can play, and say what was dropped
        ok = []
        bad = {p.split(":")[0] for p in problems}
        for i, b in enumerate(ep["beats"]):
            if f"beat {i + 1}" not in bad:
                ok.append(b)
        ep["beats"] = ok
        ep["draft_notes"] = problems
    return ep


# ----------------------------------------------------------------------
# What the scripts contain
# ----------------------------------------------------------------------

def coverage(season_id: str) -> dict:
    season, series = load(season_id), load("series")
    out = {"episodes": [], "warnings": []}
    for e in season["episodes"]:
        f = EPISODES / f"{e['id']}.json"
        row = {"id": e["id"], "number": e["number"], "title": e["title"], "scripted": f.exists(), "lines": {}, "words": {}, "quirks": {}}
        if f.exists():
            ep = json.loads(f.read_text(encoding="utf-8"))
            row["status"] = ep.get("status", "scripted")
            q = {"thought": 0, "vision": 0, "sideeye": 0, "earring": 0, "stomp": 0, "frags": 0, "meme": 0, "scenes": 0}

            def walk(beats):
                for b in beats:
                    k = b.get("k")
                    if k == "line":
                        row["lines"][b["who"]] = row["lines"].get(b["who"], 0) + 1
                        txt = " ".join(x if isinstance(x, str) else x.get("text", "") for x in b.get("frags", [b.get("text", "")]))
                        row["words"][b["who"]] = row["words"].get(b["who"], 0) + len(txt.split())
                        q["frags"] += bool(b.get("frags"))
                        q["sideeye"] += str(b.get("expr", "")).startswith("sideeye")
                        q["earring"] += b.get("earring") is True
                        q["stomp"] += bool(b.get("stomp"))
                    elif k in ("thought", "vision", "meme"):
                        q[k] += 1
                    elif k == "scene":
                        q["scenes"] += 1
                    elif k == "expr" and str(b.get("expr", "")).startswith("sideeye"):
                        q["sideeye"] += 1
                    elif k == "prop" and b.get("prop") == "earring" and b.get("on"):
                        q["earring"] += 1
                    if k == "vision":
                        walk(b.get("beats", []))
            walk(ep["beats"])
            row["quirks"] = q
            for c in series["cast"]:
                if c not in row["lines"] and c not in ("yarrow", "dusty"):
                    out["warnings"].append(f"{e['number']}: {series['cast'][c]['name']} has no lines")
            if q["thought"] > 1:
                out["warnings"].append(f"{e['number']}: {q['thought']} thought spirals (the rule is at most one)")
            if q["vision"] > 1:
                out["warnings"].append(f"{e['number']}: {q['vision']} visions (the rule is at most one)")
        else:
            out["warnings"].append(f"{e['number']} {e['title']}: no script yet")
        out["episodes"].append(row)
    for t in season["threads"]:
        missing = [e["number"] for e in season["episodes"] if t["id"] not in e.get("threads", {})]
        if len(missing) > len(season["episodes"]) // 2:
            out["warnings"].append(f"thread '{t['name']}' is quiet in {len(missing)} of {len(season['episodes'])} episodes")
    return out

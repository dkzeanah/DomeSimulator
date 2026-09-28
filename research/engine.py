"""The research engine: which dome topics people search for, and which do well.

It works from the knowledge graph's search phrases (``research/knowledge-graph
.json``, or an export of the live page's database) in two stages, and caches
everything in ``research/research.sqlite3`` so a run can stop and resume.

**Demand** -- free, no key. YouTube's own autocomplete for every phrase, and
for a few question and intent variants of it ("how to", "cost", "vs",
"diy"). Autocomplete lists what people actually type, most common first, so
it measures the size and the shape of the search space around a phrase, and
it surfaces searches the graph does not cover yet.

**Performance** -- needs ``YOUTUBE_API_KEY`` (YouTube Data API v3; free, 10,000
quota units a day; one search costs 100). For each phrase, the top 25 videos:
views, age, views per day, and the channel's subscribers. The number that
matters is the **outlier ratio**, views divided by subscribers: a video that
far outruns its channel is a topic doing the work, not an audience.

Every score is written out with its parts, so a topic's rank can be argued
with. The formula is in :func:`score`.

    py -3.12 -m research.engine demand            # autocomplete, all phrases
    py -3.12 -m research.engine performance       # needs YOUTUBE_API_KEY
    py -3.12 -m research.engine report            # markdown + graph scores
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sqlite3
import statistics
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB = HERE / "research.sqlite3"
GRAPH = HERE / "knowledge-graph.json"
OUT = HERE / "out"

SUGGEST = "https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q="
API = "https://www.googleapis.com/youtube/v3/"
#: Variants that tell apart the intents a video can serve.
INTENTS = ("", "how to ", "diy ", " cost", " vs", " mistakes", " build")
PAUSE_S = 0.35          # between autocomplete calls, to be a polite client
SEARCH_COST = 100       # quota units per search.list call
DAILY_QUOTA = 10_000


# ----------------------------------------------------------------------
# Storage
# ----------------------------------------------------------------------

def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB)
    conn.executescript("""
    create table if not exists suggest (
        query text primary key, suggestions text not null, fetched text not null);
    create table if not exists search (
        phrase text primary key, video_ids text not null, total int, fetched text not null);
    create table if not exists video (
        id text primary key, title text, channel_id text, channel_title text,
        published text, views int, likes int, comments int, duration text, fetched text);
    create table if not exists channel (
        id text primary key, title text, subscribers int, videos int, fetched text);
    """)
    return conn


def graph() -> dict:
    return json.loads(GRAPH.read_text(encoding="utf-8"))


def _get_json(url: str, timeout: float = 15.0):
    request = urllib.request.Request(url, headers={"User-Agent": "DomeSim-research/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", "replace"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ----------------------------------------------------------------------
# Demand: autocomplete
# ----------------------------------------------------------------------

def variants(phrase: str) -> list[str]:
    out = []
    for intent in INTENTS:
        q = (intent + phrase) if intent.endswith(" ") else (phrase + intent)
        out.append(q.strip())
    return list(dict.fromkeys(out))


def suggest(conn: sqlite3.Connection, query: str, refresh: bool = False) -> list[str]:
    row = conn.execute("select suggestions from suggest where query=?", (query,)).fetchone()
    if row and not refresh:
        return json.loads(row[0])
    data = _get_json(SUGGEST + urllib.parse.quote(query))
    suggestions = [s for s in data[1] if isinstance(s, str)]
    conn.execute("insert or replace into suggest values (?,?,?)",
                 (query, json.dumps(suggestions), _now()))
    conn.commit()
    time.sleep(PAUSE_S)
    return suggestions


def run_demand(refresh: bool = False, limit: int | None = None) -> dict:
    conn = connect()
    phrases = [(n["id"], s) for n in graph()["nodes"] for s in n["seeds"]]
    if limit:
        phrases = phrases[:limit]
    done = 0
    for _, phrase in phrases:
        for q in variants(phrase):
            try:
                suggest(conn, q, refresh)
            except Exception as exc:  # network: keep going, report at the end
                print(f"  ! {q}: {exc}")
        done += 1
        if done % 20 == 0:
            print(f"  {done}/{len(phrases)} phrases")
    return {"phrases": len(phrases)}


# ----------------------------------------------------------------------
# Performance: YouTube Data API
# ----------------------------------------------------------------------

def _api(path: str, **params) -> dict:
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        raise RuntimeError("set YOUTUBE_API_KEY (YouTube Data API v3) to run the performance stage")
    params["key"] = key
    return _get_json(API + path + "?" + urllib.parse.urlencode(params))


def run_performance(budget: int = DAILY_QUOTA - 500, refresh: bool = False) -> dict:
    """Search each phrase once, then fetch its videos' and channels' statistics.

    Stops before ``budget`` quota units; cached phrases cost nothing, so the
    next day's run carries on where this one stopped.
    """
    conn = connect()
    spent, searched = 0, 0
    phrases = list(dict.fromkeys(s for n in graph()["nodes"] for s in n["seeds"]))
    for phrase in phrases:
        if not refresh and conn.execute("select 1 from search where phrase=?", (phrase,)).fetchone():
            continue
        if spent + SEARCH_COST + 2 > budget:
            print(f"  quota budget reached after {searched} searches; run again tomorrow")
            break
        found = _api("search", part="id", q=phrase, type="video", maxResults=25,
                     relevanceLanguage="en", order="relevance")
        spent += SEARCH_COST
        ids = [item["id"]["videoId"] for item in found.get("items", [])]
        total = found.get("pageInfo", {}).get("totalResults")
        conn.execute("insert or replace into search values (?,?,?,?)", (phrase, json.dumps(ids), total, _now()))
        if ids:
            videos = _api("videos", part="snippet,statistics,contentDetails", id=",".join(ids))
            spent += 1
            channel_ids = set()
            for v in videos.get("items", []):
                st, sn = v.get("statistics", {}), v["snippet"]
                channel_ids.add(sn["channelId"])
                conn.execute("insert or replace into video values (?,?,?,?,?,?,?,?,?,?)", (
                    v["id"], sn["title"], sn["channelId"], sn["channelTitle"], sn["publishedAt"],
                    int(st.get("viewCount", 0)), int(st.get("likeCount", 0) or 0),
                    int(st.get("commentCount", 0) or 0), v["contentDetails"].get("duration"), _now()))
            missing = [c for c in channel_ids
                       if not conn.execute("select 1 from channel where id=?", (c,)).fetchone()]
            if missing:
                channels = _api("channels", part="snippet,statistics", id=",".join(missing[:50]))
                spent += 1
                for c in channels.get("items", []):
                    st = c.get("statistics", {})
                    conn.execute("insert or replace into channel values (?,?,?,?,?)", (
                        c["id"], c["snippet"]["title"],
                        int(st.get("subscriberCount", 0) or 0), int(st.get("videoCount", 0) or 0), _now()))
        conn.commit()
        searched += 1
    return {"searched": searched, "quota_spent": spent}


# ----------------------------------------------------------------------
# Scoring
# ----------------------------------------------------------------------

@dataclass
class VideoStat:
    title: str
    channel: str
    views: int
    age_days: float
    subscribers: int | None
    duration: str | None

    @property
    def views_per_day(self) -> float:
        return self.views / max(self.age_days, 7.0)

    @property
    def outlier(self) -> float | None:
        """Views per subscriber. Above 3, the topic outran the channel."""
        if not self.subscribers:
            return None
        return self.views / max(self.subscribers, 1000)


def phrase_videos(conn, phrase: str) -> list[VideoStat]:
    row = conn.execute("select video_ids from search where phrase=?", (phrase,)).fetchone()
    if not row:
        return []
    out = []
    now = datetime.now(timezone.utc)
    for vid in json.loads(row[0]):
        v = conn.execute("select title, channel_id, channel_title, published, views, duration "
                         "from video where id=?", (vid,)).fetchone()
        if not v:
            continue
        subs = conn.execute("select subscribers from channel where id=?", (v[1],)).fetchone()
        age = (now - datetime.fromisoformat(v[3].replace("Z", "+00:00"))).total_seconds() / 86400
        out.append(VideoStat(v[0], v[2], v[4], age, subs[0] if subs else None, v[5]))
    return out


def demand_for(conn, phrase: str) -> dict:
    """How big the search space around a phrase is, from autocomplete."""
    total, exact, completions = 0, 0, set()
    for q in variants(phrase):
        row = conn.execute("select suggestions from suggest where query=?", (q,)).fetchone()
        if not row:
            continue
        items = json.loads(row[0])
        total += len(items)
        completions.update(items)
        if q.lower() in (s.lower() for s in items[:3]):
            exact += 1
    return {"suggestions": total, "distinct": len(completions),
            "intents_answered": exact, "completions": sorted(completions)}


def score(demand: dict, videos: list[VideoStat]) -> dict:
    """One number per topic, with its parts.

    demand     distinct autocomplete completions across the intent variants
               (0-70): how much people type around it.
    vpd        median views per day of the top results: how much they watch.
    outliers   share of top results with views >= 3x their channel's
               subscribers: whether small channels break out on it.

    score = 100 x demand_part x (1 + 2 x outliers) / 3 x watch_part, where
    demand_part = distinct / 70 and watch_part = log10(1 + vpd) / 3. With no
    performance data yet the score is the demand part alone, and says so.
    """
    demand_part = min(1.0, demand["distinct"] / 70)
    if not videos:
        return {"score": round(100 * demand_part, 1), "basis": "demand only",
                "demand": demand["distinct"]}
    vpd = statistics.median(v.views_per_day for v in videos)
    ratios = [v.outlier for v in videos if v.outlier is not None]
    outliers = sum(1 for r in ratios if r >= 3) / len(ratios) if ratios else 0.0
    watch_part = min(1.0, math.log10(1 + vpd) / 3)
    best = max(videos, key=lambda v: (v.outlier or 0) * math.log10(1 + v.views))
    return {"score": round(100 * demand_part * (1 + 2 * outliers) / 3 * watch_part, 1),
            "basis": "demand + performance", "demand": demand["distinct"],
            "views_per_day": round(vpd), "outlier_rate": round(outliers, 2),
            "top_title": best.title, "top_channel": best.channel}


# ----------------------------------------------------------------------
# Report
# ----------------------------------------------------------------------

def report() -> Path:
    conn = connect()
    g = graph()
    known = {s.lower() for n in g["nodes"] for s in n["seeds"]}
    rows, discovered = [], {}
    for node in g["nodes"]:
        parts = []
        for phrase in node["seeds"]:
            d = demand_for(conn, phrase)
            s = score(d, phrase_videos(conn, phrase))
            parts.append((phrase, d, s))
            for c in d["completions"]:
                if c.lower() not in known:
                    discovered.setdefault(c, set()).add(node["label"])
        if not parts:
            continue
        best = max(parts, key=lambda p: p[2]["score"])
        rows.append((node, best, parts))
    rows.sort(key=lambda r: -r[1][2]["score"])

    OUT.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d")
    scores = {node["id"]: {**best[2], "phrase": best[0], "updated": stamp} for node, best, _ in rows}
    (OUT / "graph-scores.json").write_text(json.dumps(scores, indent=1), encoding="utf-8")

    lines = [f"# Dome topic research -- {stamp}", "",
             "Scores are relative, not absolute: they rank this project's topics against each other. "
             f"Basis: {'demand + performance' if any(s['basis'] != 'demand only' for s in scores.values()) else 'demand only (add YOUTUBE_API_KEY and run `performance` for views and breakouts)'}.",
             "", "## Topics, ranked", "",
             "| # | keyword | best phrase | score | demand | views/day | breakout rate | strongest video |",
             "|---|---|---|---|---|---|---|---|"]
    for k, (node, (phrase, d, s), _) in enumerate(rows, 1):
        lines.append(f"| {k} | {node['label']} | {phrase} | {s['score']} | {s['demand']} | "
                     f"{s.get('views_per_day', '')} | {s.get('outlier_rate', '')} | "
                     f"{s.get('top_title', '').replace('|', '/')} |")
    lines += ["", "## Searches the graph does not cover yet", "",
              "What people type around our phrases that no keyword in the graph holds. "
              "The best of these are new nodes.", ""]
    ranked = sorted(discovered.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    for text, sources in ranked[:120]:
        lines.append(f"- **{text}** -- near {', '.join(sorted(sources))}")
    path = OUT / f"topics-{stamp}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("stage", choices=("demand", "performance", "report", "all"))
    parser.add_argument("--refresh", action="store_true", help="ignore the cache")
    parser.add_argument("--limit", type=int, default=None, help="first N phrases only")
    parser.add_argument("--budget", type=int, default=DAILY_QUOTA - 500)
    args = parser.parse_args(argv)
    if args.stage in ("demand", "all"):
        print("demand:", run_demand(args.refresh, args.limit))
    if args.stage in ("performance", "all"):
        if os.environ.get("YOUTUBE_API_KEY"):
            print("performance:", run_performance(args.budget, args.refresh))
        else:
            print("performance: skipped -- no YOUTUBE_API_KEY")
    if args.stage in ("report", "all"):
        print("report:", report().relative_to(HERE.parent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

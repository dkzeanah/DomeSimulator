# Making episodes and lesson films with the web engine: a guide for an LLM

This is for an LLM, or a person, working in this repository who has to write, change, check,
play or render a film on the web engine. It covers the two kinds of film the engine makes:

- **Episodes**: the sitcom *Level With Me*, scripted as beats in `sketch_claude/episodes/`.
- **Lesson films**: narrated teaching films from `two_v_demo` lessons, such as the 2V
  Geodesic Masterclass (see `docs/web-video-engine.md`).

Read CLAUDE.md first. Its rules apply here:

- Outputs are append-only.
- Every film is a release.
- Numbers on screen are computed, never typed.
- Look at stills before a long render.

## 1. Where everything is

| Piece | File | What it does |
|---|---|---|
| The dome, the deck, the site | `sketch_claude/model.py` | `build(Spec)` solves every piece. The engine stands everything in this world. |
| The studio set (bench, jig, saw, loose panel) | `sketch_claude/episode_server.py` `set_pieces` | Shop pieces placed beside the dome. Add new set pieces here. |
| The series and cast | `sketch_claude/episodes/series.json` | Title, pace, cast: name, role, Edge TTS voice, rate and pitch, looks, colour, quirk, secret. |
| A season's plan | `sketch_claude/episodes/season01.json` | The episodes, their arcs and threads. The Season room edits it. |
| An episode | `sketch_claude/episodes/sNNeNN.json` | `{id, season, series, number, title, logline, rating, notes, beats: [...]}` |
| Writing help | `sketch_claude/writers.py` | `skeleton()` (from the season plan), `draft()` (an LLM draft), `check()` (validates an episode), `coverage()` |
| The engine | `sketch_claude/static/engine.js` | Plays beats on one virtual clock: compile, seek, play, render. Each line is timed by its real voice clip. |
| Cameras and graphics | `sketch_claude/static/cine.js` | Shots, lenses, moves, title cards, lower thirds, memes, flashes, and the program canvas that is recorded. |
| Characters and voices | `sketch_claude/static/cast.js` | Rigs, actions, expressions, walking, and fetching voices from `/api/voice`. |
| Music and sound | `sketch_claude/static/band.js` | Synthesised; nothing is sampled. |
| The visual editor | `sketch_claude/static/director.js`, `director.html` | The Episode Director, at `/director`. |
| Lesson films | `sketch_claude/lesson_web.py`, `static/lesson.js`, `static/lessonstage.js` | Lesson Studio, at `/lesson?lesson=2v`. |
| The server | `sketch_claude/server.py` | Serves the pages and the `/api/*` routes below. Bound to 127.0.0.1. |

Start the studio with `py -3.12 -m sketch_claude serve` and open http://127.0.0.1:8767.

| Page | Address |
|---|---|
| Modeller | `/` |
| Episode Director | `/director?episode=s01e03` |
| Season room | `/season` |
| Lesson Studio | `/lesson?lesson=2v` |

## 2. An episode is a list of beats

Beats run in order. A beat that takes time (a line, a wait, a card, a walk with `wait: true`)
holds the clock. Everything else happens at once and the next beat follows. The fields below
are the ones the ten season-one scripts use, so they are the ones the engine reads
(`engine.js`, `beat()`):

| `k` | Fields | What it does |
|---|---|---|
| `scene` | `name, at, mood, sun:[az,el], place:{who:[x,y,yaw]}, view:{step,explode,tagsOff}, panelOnBench?, hide?` | Starts a scene: location (`studio`, `patio`, `yard`, `hedge`, `inside`), light, and where each character stands. |
| `line` | `who, text` or `frags:[{text,rate,pause}], act, cam, expr?, pad?, after?, earring?, stomp?, keepExpr?` | A spoken line. Its length is its voice clip's. `frags` speak in pieces, stop and go. `cam` sets the shot for it. |
| `cam` | `cam:{kind, ...}, dur, wait` | A shot. `kind` is `single`, `two`, `ots`, `wide`, `low` or `move`. A move is one of `hold`, `dollyIn`, `dollyOut`, `orbit`, `slide`, `pan`, `crane`, `pedestal`, `dollyZoom`, `reveal`, `flyover`, `spiral`. |
| `act` | `who, act` | An action: talk, point, wave, shrug, hammer, carry, measure, sit, fall, and the rest (`ACTS` in engine.js). |
| `walk` | `who, to:[x,y] or a landmark, speed, wait` | Walks there. |
| `face`, `place`, `expr`, `prop` | `who` plus `at`, `at:[x,y,yaw]`, `expr`, or `prop`+`on` | Turn to face something, stand somewhere, change expression, or hold a prop (phone, earring). |
| `card` | `text, sub, secs, music` | A full title card. |
| `lower` | `who` | That character's lower third (name and role). |
| `figure` | `big, small, secs` | A number on screen. `{{tokens}}` fill from the model's figures, so it is computed, never typed. |
| `meme` | `style, text, secs, sfx?, who?` | `style` is `caption`, `zoom`, `freeze` or `pov`. |
| `thought` | `who, title, frags, ghosts` | Inside a head: an inner voice and its ghosts. |
| `vision` | `who, label, beats:[...]` | A vision: nested beats played in a dream grade. |
| `music` | `name, secs, mood?, motif?` | `pad`, `tension`, `piano`, `heart`, `rain`, or `theme` with `bars`. |
| `sfx` | `name` | `rimshot`, `chime`, `thud`, `clatter`, `snap`, `stomp`, `boom`, `scratch`, `airhorn`, `saw`. |
| `wait` | `s` | Hold, in seconds. |
| `flash` | `secs, sfx?` | A white flash. |
| `build` | `from, to, every` | Steps the dome's build stages. |
| `mood` | `mood` | Relights mid-scene: `day`, `golden`, `dusk`, `night`, `overcast`, `storm`. |
| `view` | `view:{step, explode, tagsOff}` | Changes how the dome shows. |
| `gag`, `credits` | `name, who` / `secs` | A running gag, or the end credits. |

The quickest correct beat is a copy of a real one. The Director's **+ Add** inserts any kind,
starting from the first beat of that kind in the season's own scripts.

## 3. Writing or changing an episode

1. **From the season plan:** `POST /api/season/season01/skeleton {"episode": "s01e11"}` lays
   out the beats from the season room's outline. `POST .../draft` asks an LLM for a draft. Both
   keep the old file as a version.
2. **By hand or by an LLM:** edit `sketch_claude/episodes/s01eNN.json` directly. Keep `id`,
   `number` and `title`. Characters must exist in `series.json`. A location must be one the
   world builds.
3. **Validate:** `writers.check(episode, series)` returns a list of problems. An empty list
   means it plays.
4. **In the Director** (`/director?episode=s01eNN`):
   - **Outline:** scene by scene, with each scene's cast and every beat's time. Drag a beat to
     move it, or use **+ Add** for any kind.
   - **Inspector:** form fields for lines (speaker, words, pace, face, action, camera) and JSON
     for every other beat.
   - **Script, Cast, Analysis:** the script view, hearing a voice, and the line counts and
     coverage.
   - **Camera:** free camera and lens.
   - **Storyboard:** a thumbnail at every shot.
   - **Re-time:** times the episode from its voices again.
   - **Save** keeps the previous version in `episodes/.versions/`. **Save as new episode**
     makes `s01e11` and so on.

## 4. Playing and rendering

| Do this | Command or place |
|---|---|
| Play and scrub, with sound | The Director: Space plays, `[` and `]` step between shots. |
| A thumbnail per shot | The Director's **Storyboard** button. |
| Render an episode, no window | `py -3.12 -m sketch_claude episode --episode s01e03` (add `--draft` to render into tmp/) |
| Render from the Director | Render tab: **Render here**, or **Start a job** |
| A lesson film's stills | `py -3.12 -m film stills 2v --engine web` (both orientations, in tmp/lesson-stills/2v/) |
| A lesson film | `py -3.12 -m film make 2v --engine web` |

A finished render is a new numbered folder in `deliverables/`:

- the landscape cut, at 1920x1080;
- the phone cut;
- captions;
- a thumbnail per scene;
- `description.md`.

Lesson films also get `release/`, made by `two_v_demo.release.build_release`.

**Check before a long render:**
1. `writers.check` returns nothing.
2. The Director's timeline shows no gaps you did not mean.
3. Look at the storyboard, or at the stills for a lesson.
4. Hear the cast tab's voice for any new character.

## 5. Adding digital elements

| To add | Do this |
|---|---|
| A set piece (a bench, a saw, a prop table) | Write a function in `sketch_claude/shop.py` that returns pieces, and place it in `episode_server.set_pieces` with `_place(pieces, at, yaw)`. It then stands in every scene. |
| A landmark a camera or a walk can name | The `landmarks` that `model.build` returns. Read `world.landmarks` in `set.js` and the engine. |
| A character | Add an entry to `series.json` `cast` (voice, rate, pitch, looks, colour). `cast.js` builds the rig from it. |
| A sound | Add a method to `Band` in `band.js` (sines, noise and envelopes; nothing sampled), then name it in an `sfx` or `music` beat. |
| A new kind of beat | Add a `case` in `Engine.beat()` in engine.js, and the kind's name to `KIND_NAMES` in director.js. |
| A number on screen | A `figure` beat whose text uses `{{tokens}}` from `setData.figures` (`episode_server.set_pieces`). Never type the number. |
| A lesson film's pictures | `docs/web-video-engine.md`, "Moving a film over". |

## 6. Publishing

1. `py -3.12 website/scripts/export_episodes.py` lists what `/episodes` will show.
2. `--prepare`, then `--upload --remote`, publish the films.
3. Push to the `staging` branch. Check https://staging.zeanahlab.pages.dev.
4. Promote from Admin, Tools and releases, or with the GitHub Actions button.

## 7. The project agent

The agent has these tools (`project_agent/web_engine.py`):

| Tool | What it does |
|---|---|
| `web_episodes` | Lists the episodes and validates one. |
| `web_episode_render` | Renders an episode headless. |
| `web_lesson` | Makes a lesson film's stills or the film. |

The `episode` recipe runs the whole loop: validate, render a draft, check the draft's folder,
render the release, and check the release.

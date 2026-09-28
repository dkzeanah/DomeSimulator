# The re-render queue: every film, re-made in the Cabin World

The **Cabin World** is the baseline scene from here on: the hilltop at sunset, the
raw-wedge simulator's own 2V dome on its pad with two crown triangles still to go up,
the builder, and in the foreground the log (growth rings, eight rip cuts), the stump
with the chainsaw, the stack of members. It lives in `two_v_demo/cabin_world.py`;
the cold open (`wedge_book/cold_open.py`) was its first film.

This folder turns every film the project has already rendered into a checklist to be
re-made in that world, one at a time, by any session of Claude or any other model.
**The originals are never modified** -- a re-render is always a new lesson and a new
file.

## For a person

Open the launcher, **Films & media → Re-render Queue**. Pick a film, press
**Copy prompt**, paste it into Claude (or another AI) in this repository. When the
film comes back for review, watch it, then set its status to `done` (or back to
`todo` with a note saying what is wrong).

**Copy 'next in queue' prompt** gives a session the next open film without you
choosing one.

## For a model

Everything is one command line:

```bash
py -3.12 -m rerender list                 # every film and its status
py -3.12 -m rerender next                 # the next open item
py -3.12 -m rerender prompt KEY           # the full blueprint for one film -- follow it
py -3.12 -m rerender claim KEY --by NAME  # before you start; refused if someone has it
py -3.12 -m rerender note KEY "text" --by NAME
py -3.12 -m rerender status KEY review --by NAME --output PATH ...
```

The blueprint (`prompt KEY`) is regenerated from the repository every time: the house
rules from `CLAUDE.md`, the Cabin World's API and landmarks as they stand, the film's
chapters in full (narration, figures, callouts), the modules its numbers come from,
the commands to take stills and export, the definition of done, and this film's
history in the queue.

## Files

| file | what | edit by hand? |
|---|---|---|
| `catalogue.json` | every film, read out of the code that made it | no -- `py -3.12 -m rerender refresh` |
| `queue.json` | status, owner, priority, notes, outputs per film | no -- use the command line or launcher |
| `prompts/` | the last blueprint written for each film | no -- regenerated on every copy |
| `catalogue.py` | how films are found; `FAMILIES` and `FIT` tables | yes, for those two tables |
| `state.py` | claims, statuses, the originals guard | |
| `blueprint.py` | what goes into a prompt | yes, to change the instructions |

## How it stays honest

* **No double work.** A claim is refused while another worker holds the item; a claim
  untouched for 12 hours is treated as abandoned.
* **Originals untouched.** A claim records every original's size and date; `review`
  and `done` are refused if one changed.
* **Nothing typed twice.** Chapters, titles and numbers are read from the lessons,
  presentations and slideshow scripts, so the queue cannot drift from the films.
  Refresh after a film is added.
* **Only the user marks `done`.** Models stop at `review`.

## The worked example

`two_v_demo/lesson_cabin_pilot.py` is a complete two-chapter film in the Cabin World,
rendered through the standard masterclass exporter: `cabin_world.paint(app)` in each
painter, `ground="off"`, `backdrop=cabin_world.backdrop`, `light=cabin_world.LIGHT`,
cameras from `two_v_demo/shots.py` aimed at `cabin_world.landmarks()`. Every
re-render starts as a copy of it.

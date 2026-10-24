# The web video engine

Films can now be rendered in the browser engine (`sketch_claude`, three.js) instead of
the moderngl renderer (`two_v_demo/app.py`). The moderngl engine is unchanged and is
still the default. The 2V Geodesic Masterclass is the first film made on the web engine.

```
py -3.12 -m film stills 2v --engine web     # one still per chapter, landscape and phone
py -3.12 -m film make 2v --engine web       # the release
```

(`py -3.12 -m sketch_claude lesson 2v [--stills] [--draft]` is the same thing.)

## What carried over from the moderngl engine, and where it lives now

| Lesson learned | How the web engine keeps it |
|---|---|
| The words are the lesson's own | The chapters, promises and narration come straight from the `two_v_demo` Lesson. Nothing is rewritten for the web. |
| The house voice and timing | Each chapter is one clip of `audio.spoken_chapter_text`, in `audio.DEFAULT_VOICE` at the lesson's rate. A chapter lasts its authored length or `SPEECH_DELAY + speech + TAIL_PADDING`, whichever is longer. Same rule as the exporter. |
| Chapter timestamps must be true | The narration plan records the stretched lengths, and `release.chapter_marks` reads them. |
| Numbers on screen are computed | A lesson with a web stage brings its equations from code (2V: `two_v_demo.geometry`, in `lesson_web.equations_2v`). "computed by" shows only where a computed number is on screen. |
| Every render is a release | Landscape cut, phone cut, both caption files, narration script, review JSON, and `release.build_release`: thumbnails per chapter, plus YouTube, Facebook and Instagram copy. |
| Beat number top-left on every frame | Drawn in `lesson.js` `overlays()`, with the chapter count. |
| Phone cut framing | The phone cut is its own pass at 1080x1920 with a portrait layout, not a crop. Each stage declares its subject's width, and the camera stands back far enough for it to fit the room the graphics leave. |
| Look before rendering | `--stills` draws one frame per chapter in both orientations into `tmp/lesson-stills/<lesson>/`, in seconds. |
| Music is made, not sampled | `score.compose(bed=True)` sits under the voice and dips while it speaks. |
| Frame-exact, whatever the machine | A frame is a pure function of film time. The frames go through the Director's render pipe (`episode_server.render_start/render_frame`). |
| Captions match the release | The burned-in captions are the release's own SRT cues (`narration.subtitle_file`), parsed back. |

## Moving a film over

Any lesson renders on the web engine today. A lesson without a web stage of its own gets
the generic stage: the solver's wedge dome, coloured by edge class, slowly turning. To give
a film its own pictures:

1. Write its stage data and computed equations in `sketch_claude/lesson_web.py` and add it
   to `WEB_STAGES`. Take the data from the module that computes it; never type a figure.
2. Add a `build_<stage>(g)` to `static/lessonstage.js` for every `Chapter.stage` the lesson
   uses. Each returns `pose(progress, time)`. Pose what you built (`moveStruts`,
   `moveNodes`); never allocate a mesh per frame.
3. Add its framing to `Stage.frame()`: the target, the distance, the subject's half-width,
   and a fixed camera direction if a diagram must be seen square.
4. Run `film stills <lesson> --engine web`, look at every still in both orientations, then
   `film make <lesson> --engine web`.

The switch is complete when every film in `two_v_demo/deliverables.py` has a web stage.
Then `film make` can default to `--engine web`, and `two_v_demo/app.py` can be retired.
Until then, both engines stay.

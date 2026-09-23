# Vertical cuts and teasers

Every film in this repository can now come out two ways: the horizontal cut it
was made as, and a vertical cut for phones (Shorts, Reels, TikTok). And every
film has a teaser: a thirty-to-forty-second hype cut built out of the film
itself.

**All of that is what one render means now.** An export produces the
landscape cut, the phone cut beside it, the release folder of
per-chapter thumbnails and platform copy, *and* the teaser — without
anybody asking for any of it. The teaser used to be a separate thing
somebody had to remember, which is why most films did not have one.
`teaser=False` in a ticket is the only way to skip it, and that flag
exists so the teaser's own ticket can set it and not recurse. A render
that goes through `_export_both` passes `release=False, teaser=False`
to both children, so the pair produces one teaser and one release
folder between them rather than three of each.

**Two things a painter has to know about the vertical cut**, because
neither shows up in a landscape still:

* **Scenery must be marked.** The phone cut re-fits the camera to what
  was painted, and it measures every Creator draw request. Anything you
  draw as context rather than as subject needs
  `creator.draw(app, thing, backdrop=True)`, or the fit frames the
  context and shrinks the subject to nothing.
  `creator.environment()` already excludes itself.
* **Labels get dropped, not stacked.** `portrait_ui` budgets the picture
  area world labels may cover, drops what the resolver reports as
  unplaceable, and re-resolves the survivors so they spread into the
  freed room. If a label you wanted goes missing, the fix is fewer
  labels in that painter, not a bigger budget — and the drop is written
  to `plan.steps`, so the render log names it.

Every chapter also carries its **beat number** in the top left
(`03 /27`), in both orientations, so feedback on a cut can name a beat.

Nothing about the horizontal films changes. A film shown in the shape it was
made for takes exactly the path it always did, and re-renders pixel for pixel
as it shipped. That was checked on sixteen chapters across every overlay style
before and after the change.

## Making a vertical cut

The simplest way: export with `orientation` set in the render ticket.

| `orientation` | What you get |
|---|---|
| *(not set)* | Exactly what you got before. |
| `landscape` | 1920 x 1080. |
| `portrait` | 1080 x 1920, re-fitted for a phone. |
| `both` | The horizontal cut, then the vertical one, as two files: `name.mp4` and `name-vertical.mp4`. The vertical cut replays the horizontal cut's narration, so both say the same words at the same moments and the voice is only made once. |

Beats work too: `render_beats` with `orientation: portrait` renders a separate
beat library (`beats/<film>-portrait/`), never mixed into the horizontal one.

## What changes in a vertical cut, and why

A landscape film puts its words **beside** the picture. A phone has no beside,
only above and below. So on a phone:

- **Text stacks.** A header at the top (which chapter, its title), the picture in
  the middle, and the words that carry the chapter at the bottom: the teaching
  card, the math worksheet, or the montage headline. They are set large enough to
  read on a phone, and kept clear of the areas a phone app covers with its own
  buttons and captions.
- **The picture is fitted, not cropped.** After each frame is painted, the
  renderer knows where every part of the subject is. If the subject no longer fits
  the space the text leaves, the film's own camera backs away along its own line
  of sight and the lens shifts so the subject sits in the middle of that space.
  It never zooms *in* past what the film chose, so a film is given room, never
  re-directed. Only what the original frame actually showed counts as the subject:
  a wall the director left out of frame stays out.
- **Crowding is resolved step by step.** Labels, callouts and panels are boxes
  with priorities. The resolver first *pushes* each box inside the frame, then
  *shoves* the less important of any two overlapping boxes out of the way,
  *elongates* text that is too wide by re-wrapping it narrower and taller, and
  finally *compresses* anything that still cannot fit, never below a minimum size.
  Every decision is logged.
- **Callouts get their own band.** When a chapter's numbers arrive on screen, the
  picture moves up and the numbers take the band beneath it, instead of sitting on
  top of the dome.
- **Long worksheets scroll.** On a phone, a math screen shrinks its type only to a
  readable minimum. Past that, the panel grows, then the oldest settled lines
  scroll away and the newest stay.
- **The presenter controls are gone** from vertical cuts. They are for live
  presenting, not for a video.

The films already made vertically (the micro-dramas) work the same way in
reverse: on a wide screen they are left exactly as directed, because a wider
screen at the same lens only shows more at the sides.

A lesson can opt out with `frame_fit="off"`. The book's plates do this, because
they compose their own shots for each page size.

## Teasers

Each teaser runs in this order:

1. **A hook** that states the film's sharpest claim with its number, for example
   *"Sawn: 45% kept. Split: 87.4%."*
2. **Three to five beats.** Each is a real chapter of the film, played at pace
   from the part where something happens, with a steady push-in.
3. **A call to action** over the share scene the films already end on. Its words
   depend on the kind of film: a worked-number film says "every number, worked
   on screen"; a montage says "watch the whole thing"; a drama says "watch the
   episode".
4. **An ask** over the same contact card every video ends with, for example
   "Where would you build one?"

Every number in a teaser comes from the code, like the rest of the films. Seven
films (why, harvest, pine_value, why_build, 2v, world, scratch) have hand-written
hooks in `two_v_demo/teasers.py`. Every other film gets a teaser built from its
own chapters, which is honest if plainer, and trimmed to stay under 58 seconds.

```bash
py -3.12 -m two_v_demo.teasers --list
```

That prints every film's teaser copy, to read before anything renders. Then look
at stills of one teaser, one per beat in each shape:

```bash
py -3.12 -m two_v_demo.teasers --lesson why --stills
```

Then render it, narrated, in both shapes:

```bash
py -3.12 -m two_v_demo.teasers --lesson why
```

Teasers are written to `deliverables/teasers/`, as `<film>-teaser.mp4` and
`<film>-teaser-vertical.mp4`. Like every render, they never overwrite: a
re-render becomes `-v2`.

To give a film a better hook, add a `TeaserSpec` for it to `SPECS` in
`two_v_demo/teasers.py`. Name the chapters to borrow, and write the lines with
tokens such as `{{tree.recovery_pct}}` instead of typed numbers.

## Known limits

- A very wide subject, such as all twelve Dome Creator designs in a row, gets
  small in a vertical frame. It is shown whole rather than cropped.
- The share scene's burst of little domes runs off the sides of a phone frame.
  It is a burst, so that reads as intended.
- A teaser borrows a chapter's painter and camera. A chapter whose painter reads
  the film's clock directly, rather than its own progress, plays its own moment
  rather than the window the beat asks for.

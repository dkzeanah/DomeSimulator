# Video Review

Open **DomeSim Launcher → Video Review → Open Video Review**, or double-click
`Start-Video-Review.cmd` in the project root. The workbench opens in your browser.
Keep its Python process running while reviewing. There is no account, API key,
upload, or extra package installation for the review workbench itself.

## The review loop

1. **New review**: choose a video anywhere inside the DomeSim project. Name the
   review and, if available, add the original generation prompt. A new render's
   companion `*-review.json` supplies its lesson, narration, measured chapter
   timing and render settings. Older videos can import `storyboard.json`,
   `narration.md`, `*-narration.md`, `plan.json` and `*-narration-plan.json`.
   You can also paste a script and enter a lesson key such as `2v` or `byod`.
   A manually linked lesson snapshots its current narration; compare it with
   the old video before editing. Measured timing is used when available;
   authored chapter durations are never assumed to match an old render.
2. **Watch and annotate**: press **N** or **Note at playhead**. The timestamp is
   captured immediately. Uncheck **Pause when starting a note** to keep watching
   while you type. Choose a note type, priority, optional chapter and optional
   end time, then **Save note** or **Ctrl+Enter**. Click a timestamp to jump back.
   Arrow keys seek five seconds; Space plays/pauses outside text fields.
3. **Exact script edits**: choose **Narration / script**. Select a chapter and
   **Use chapter narration**, or enter a unique exact excerpt in **Original
   text**. Enter the desired replacement. For a video with only a pasted script,
   the excerpt must occur exactly once in that script. Notes without replacement
   text remain editorial tasks. Conflicting replacements produce an error for
   you to reconcile; the system does not guess which one you meant.
4. **Generate handoff**: saves a new numbered snapshot with these files:

   | File | Purpose |
   | --- | --- |
   | `action-list.md` | Timestamped tasks, priorities, keeps and verification items |
   | `script-before.md` | This round's starting narration |
   | `script-updated.md` | Narration with the exact replacements applied |
   | `next-build-prompt.md` | Original prompt plus this iteration's instructions |
   | `revision.json` | Structured notes, parent link and cumulative narration overrides |

   Open/download them in **Build handoffs**, or use **Copy next-build prompt**.
   Give the prompt to your next coding/generation session. Visual changes,
   camera changes, cuts, audio changes and pacing requests are production tasks
   for that session to implement. The workbench does not infer arbitrary code
   changes from free text. Exact narration replacements are directly consumable
   by the renderer.
5. **Build and return**: after implementing the production tasks, render the new
   version. Click **Attach next render**, choose its new file and the handoff it
   was built from. This creates the next round and preserves the earlier one.
   Open notes carry forward. Applied narration edits become **Verify in this
   render**. Resolve them only after checking the new video. Carried notes keep
   their original round/timestamp; they are not silently placed at the same time
   in an edited video. Editing a carried note lets you assign its new time.

Repeat for as many rounds as needed; there is no eight-round limit. The round
picker lets you revisit any previous video, notes, script and handoffs. Earlier
rounds are read-only. Edits/status changes append events, and generating another
handoff never rewrites the previous packet. Browser drafts survive a reload;
**Save note** commits them to disk. If two windows edit the same review, a stale
save is rejected until you reload, preserving both the history and your draft.

## Feed the handoff into a render

For Masterclass, choose the lesson and **Review packet** in the launcher, set
Action to `export_video`, and choose a fresh output filename. Narration changes
are applied to an in-memory lesson; its Python source is untouched. The renderer
checks the original text and word-cued callouts before rendering. Existing audio
with different words is rejected; regenerate narration for the new script.

The handoff also includes this command, runnable from the project root:

```powershell
py -3.12 video_review.py render --packet "video_reviews/<review>/round-0001/packet-0001/revision.json"
```

This explicitly starts the normal Masterclass renderer using saved settings,
creates a fresh `renders/render-NNNN/video.mp4` beneath the packet, then attaches
the successful result as the next review round. It does not implement the
packet's free-text production tasks. `--output`, `--size` and `--fps` can override
the destination, dimensions and frame rate. The render environment needs the
usual graphics/FFmpeg dependencies. Its normal neural narrator uses the online
speech service; review and handoff generation are offline.

The staged BYOD renderer accepts the same packet:

```powershell
py -3.12 render_bring_your_own_dome.py all --review-packet "video_reviews/<review>/round-0001/packet-0001/revision.json"
```

Its existing numbered output folders preserve prior renders. Attach its final
MP4 with **Attach next render**. For videos from other generators, use the prompt,
script and action list directly, then attach the new video in the same way.

## Storage and validation

`video_reviews/<review-id>/project.json` preserves the original prompt, script
and chapter snapshot. Each `round-NNNN` holds a video reference, script snapshot,
numbered annotation events and `packet-NNNN` handoffs. Video files are referenced,
not duplicated; keep earlier renders at their original paths. The player refuses
to substitute a file whose size or modification time changed. Back up this
folder **and** your video files. `video_reviews/` is ignored by Git.

The server binds only to `127.0.0.1`, accepts project-local video paths and
streams byte ranges for seeking. It does not execute commands from annotations,
prompts or HTTP requests. Handoffs do not automatically start renders.

Offline regression checks:

```powershell
py -3.12 -m unittest video_review.test_review -v
```

For a server without opening a browser automatically:

```powershell
py -3.12 video_review.py serve --no-browser --port 8765
```

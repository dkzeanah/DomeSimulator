# The authoring pack — teach a local model to write a film

This folder is what you paste into an Ollama model so it can write a new
DomeSim film, and the runner that plays whatever it gives you back.

| file | what it is |
|---|---|
| `PROMPT.md` | the paste-ready prompt. Regenerate it, never hand-edit it |
| `example_lesson.py` | a complete film in one file, proven to render |
| `render_lesson.py` | plays any lesson module without registering it |
| `visual-language.md` | the human reference: everything you can build with |
| `__init__.py` | builds `PROMPT.md` from the live repository |

## Why generate the prompt instead of writing it once

The prompt states what colours exist, what ready-made objects exist, what the
chapter fields are, and which functions can produce a number. All of that is
read out of the repository when the prompt is built. Add a visual object
tomorrow and the next prompt knows about it; a hand-written prompt would still
be describing last month's repository, and the model would write code against
a tool that no longer exists.

```powershell
py -3.12 -m project_agent authoring --out project_agent\authoring\PROMPT.md
```

About 2,900 words — roughly 3,900 tokens — so it fits a 7B model's context
with plenty of room for the answer.

## Which of your models to use

| model | use it for |
|---|---|
| **qwen2.5-coder:7b** | **writing the lesson file. This is the one.** |
| llama3.1 | second choice for code; better prose, weaker structure |
| deepseek-r1:7b | will reason at length first; strip its thinking before saving |
| qwen3-vl:4b, granite3.2-vision:2b | *looking at the stills you render* — ask them what is wrong with a frame |
| embeddinggemma | embeddings only; no use here |

The vision models are genuinely useful at the review step: render the stills,
then show one to `qwen3-vl:4b` and ask whether any text overlaps or anything is
cut off at the edges.

## The loop, end to end

**1. Build the prompt with your subject in it.**

```powershell
py -3.12 -m project_agent authoring --brief "A three-chapter film about why a dome needs only two strut lengths, for someone who has never built anything." --out prompt.md
```

**2. Hand it to the model.**

```powershell
Get-Content prompt.md | ollama run qwen2.5-coder:7b > draft.py
```

(cmd.exe: `ollama run qwen2.5-coder:7b < prompt.md > draft.py`)

**3. Clean the answer.** Models wrap code in markdown fences and sometimes
chat before it. Keep only the Python, starting at the docstring. The file's
own docstring says where it goes:

```
SAVE THIS AS: two_v_demo/lesson_<key>.py
```

**4. Prove it before you render it.**

```powershell
py -3.12 project_agent\authoring\render_lesson.py --module two_v_demo.lesson_<key> --selftest
```

This runs `lesson.validate()` and the file's own selftest. Most model mistakes
die here, in seconds, with a clear message.

**5. Look at it.**

```powershell
py -3.12 project_agent\authoring\render_lesson.py --module two_v_demo.lesson_<key> --chapter-stills
```

One PNG per chapter in `two_v_demo_output\<key>\`. Open them. This is the step
that catches the things a selftest cannot: a camera inside the subject, labels
on top of each other, a row laid into the screen instead of across it.

**6. Only then, export.**

```powershell
py -3.12 project_agent\authoring\render_lesson.py --module two_v_demo.lesson_<key> --export exports\<key>.mp4
```

Add `--silent` for a fast, voiceless pass to check motion. Exports are
append-only: pointing at an existing file writes `-v2` beside it.

## Exporting with nothing but that one file

That is what `render_lesson.py` is for. It imports your module, finds the
`Lesson` object in it by type, validates it, builds the renderer, and calls
the exporter directly. No registry entry, no deliverables row, no launcher
preset — nothing else in the repository needs to know your film exists.

What you give up by staying unregistered: it will not appear in the launcher's
Masterclass tab, `render_all` will not rebuild it, and the deliverables table
will not track it. When a film is worth keeping, register it properly — the
agent does all three files under backup and rollback:

```powershell
py -3.12 -m project_agent produce film key=<key> title="<Title>"
```

## What the model will get wrong, and how you will know

| symptom | cause | fix |
|---|---|---|
| `AssertionError` in the selftest | its own validate caught a bad claim | usually the number is wrong, not the assert |
| sticks recede into the screen | a row laid along Y | lay it along X |
| an empty bordered panel | chapter `equations=()` | give it lines, or accept the empty panel |
| labels stacked on each other | many labels near one point | `label_layout="declutter"`, or spread them in Z |
| `ImportError` on a facts module | it invented a function | check the facts table in the prompt |
| numbers typed into captions | it ignored rule 1 | reject it; that is the one rule with no exceptions |

The last one matters most. A model will happily write `"$4,200 per dome"` into
a label. Every figure has to come from a function that can be re-run, or the
film is just a nicely rendered opinion.

# Concept cards: turning a video you ingested into a dome film

This is written for the model that ingests and transcribes YouTube videos (you).
The DomeSim project builds geodesic wedge domes -- a 2V dome framed from split
logs, with a service channel in every seam -- and films every idea in one 3-D
world, the **Cabin World**: a hilltop at sunset, the dome on its deck, and an
exhibit platform where each concept is shown.

**You do not write rendering code.** For each concept worth carrying over from a
video, you write one **concept card**: a JSON file. The DomeSim repository checks
it, computes its figures, and films it -- narrated, captioned, landscape and
phone cuts -- with no other step.

## What makes a concept worth a card

A card is worth writing when the video's idea can **change or explain something
in the dome**. Say which part (`dome_fit.slot`):

| slot | what it is in the dome |
|---|---|
| `seam_channel` | the V channel in every seam: water, wire, air, the three-way gate, the desiccant cartridge |
| `utility_core` | the service column: water, drain, power, controls |
| `air` | ventilation, the pressure barrier, dehumidifying, cooling |
| `water` | rain off the roof, the tank, filtering, condensing |
| `power` | solar, the battery, loads, metering |
| `skin` | the layers over the frame: shell, insulation, the hull |
| `pad` | the deck the dome stands on, piers, the network of pads |
| `frame` | the wedge members, seams, keys and joints |
| `timber` | the tree, the log, the chainsaw rip, yield and value |
| `site` | the hilltop, networks of domes, hosts and tenants |

## The four rules (the card is rejected if it breaks one)

1. **Every number has a kind and a source.** `kind` is one of:
   - `measured`: someone measured it;
   - `claimed`: the video said it, so its `source` **must include the timestamp**, e.g. `"12:34 -- he says the bed holds a fifth of its weight in water"`;
   - `standard`: a textbook or physical constant, with its reference;
   - `estimate`: your assumption, with the reason.
2. **No typed digits in any sentence.** Numbers enter narration only as
   `{name}` placeholders, filled from the card's numbers and figures. Write
   "it boils at {boil_c} degrees", never "it boils at 20 degrees". (The only
   digits allowed are "2V"-style dome words.)
3. **Figures are arithmetic, not typed.** A figure is an `expr` over numbers
   defined above it: `+ - * / **`, parentheses, and `min max abs round sqrt log10 exp pi`.
   The repository evaluates it; nothing else can run.
4. **Say what it will not do.** `limits` must hold at least one sentence with a
   number that does not flatter the idea. The dome project puts the
   unflattering number on screen on purpose.

## Size it against *this* dome

A figure may use the dome's own computed numbers by name. The current values
are in `dome_facts.json` in this pack. The names are:

`dome_radius_ft`, `dome_floor_sqft`, `dome_shell_sqft`, `dome_volume_cuft`,
`dome_members`, `dome_seams`, `dome_seam_ft`, `dome_air_cfm` (the ventilation it
needs), `dome_channel_in2` and `dome_channel_round_in` (room inside one seam's
key), `dome_peltier_w` and `dome_peltier_gal_year` (the seam's thermoelectric
plates and the water they condense), `dome_rain_gal_per_inch`, `dome_work_hours`.

That is what turns "a video about X" into "what X would do for this dome".

## The card

```jsonc
{
  "schema": 1,
  "slug": "molecular-sieve-fridge",          // kebab-case, unique
  "status": "draft",                         // draft -> ready (the owner decides); "example" = never filmed
  "title": "The fridge with no compressor",  // the film's title
  "hook": "One line that makes someone stay.",
  "source": {"url": "...", "title": "...", "channel": "...", "transcript_file": "...", "retrieved": "2026-09-28"},
  "summary": "What it is, in plain words, as narration (placeholders allowed).",
  "numbers": [ {"name": "bed_kg", "label": "zeolite in the bed", "value": 20, "unit": "kg",
                "kind": "claimed", "source": "04:10 -- 'this one holds twenty kilos'", "why": "sets the scale",
                "format": ".0f"} ],
  "figures": [ {"name": "water_per_cycle_kg", "label": "water one bed moves",
                "expr": "bed_kg * uptake_kg_per_kg", "unit": "kg", "format": ".1f"} ],
  "shapes":  [ ... what to show, see below ... ],
  "beats":   [ {"title": "...", "promise": "...", "narration": "... {water_per_cycle_kg} ...",
                "show": ["bed", "evap"], "figures": ["water_per_cycle_kg"]} ],
  "dome_fit": {"slot": "seam_channel", "narration": "... {vs_peltier} times ...",
               "figures": ["vs_peltier", "dome_peltier_gal_year"]},
  "limits":  [ {"narration": "... only {cooling_avg_w} watts ...", "figures": ["cooling_avg_w"]} ],
  "hashtags": ["#zeolite", "#solarcooling"]
}
```

The film is always:
1. the concept, from `summary`;
2. **the numbers we are working from**, every number with its kind;
3. one chapter per `beat`;
4. where it fits the dome;
5. what it will not do.

Aim for three to six beats of 40–90 words each.

### Shapes: what to put on the exhibit platform

Coordinates are in stage units. The platform is about 14 units across, centred
on the origin, with z up; keep things within x, y of ±6 and z of 0–7. The
repository scales the stage onto the platform and films it.

| type | fields |
|---|---|
| `box` | `at` (centre), `size` [x, y, z] |
| `cylinder` | `at` (one end), `to` (other end), `radius` |
| `sphere` | `at`, `radius` |
| `cone` | `at` (base), `to` (tip), `radius` |
| `arrow` | `at`, `to`, `radius` (thin, like 0.08) |
| `disc` | `at`, `radius` (flat, facing up) |
| `flow` | `path` [[x,y,z], ...], `count`, `radius`, `speed`: moving particles for heat, air, vapour or water |
| `label` | `at`, `text` |

Every shape takes:
- `id`: used by a beat's `show` list;
- `color`: a name from steel, copper, wood, water, cold, heat, air, vapour, glass, white, dark, solar, warn, ok, amber, or an [r, g, b] list from 0 to 1;
- `alpha` below 1 makes it see-through;
- `label` puts a caption on it, with an optional `label_offset`;
- `"always": true` keeps it in every beat.

Build the *mechanism*, not a picture: vessels as cylinders, beds and boxes as
boxes, flows as `flow` paths between them. A beat's `show` list reveals the
parts as the story adds them.

## How you know it worked

The owner (or a Claude session in the repository) runs:

```bash
py -3.12 -m concepts check concepts/cards/<slug>.json
py -3.12 -m rerender stills concept_<slug>
py -3.12 -m rerender render concept_<slug>
```

The first command prints every problem with its reason. Put your cards in
`concepts/cards/` (or hand them over to be placed there). Mark a card `ready`
only when the owner agrees. Until then, `draft` cards are checked but not filmed.

## What is in this pack

| file | what it is |
|---|---|
| `README.md` | this guide |
| `dome_facts.json` | the dome's own numbers you may use by name, with their current values, and the slots |
| `example-molecular-sieve-fridge.json` | a complete card to copy the shape of |
| `reference/card.py` | the exact checker your cards go through -- read it to see every rule; you do not need to run it |
| `reference/knowledge-graph.json` | the project's topics and search phrases -- link your concept to the nearest ones in your notes |
| `reference/CLAUDE.md` | the project's house rules, for context |

## A worked example

`example-molecular-sieve-fridge.json` in this pack is complete. It uses
textbook values marked `estimate` and `standard`, because no transcript was
attached; a real card from a transcript would mark the video's numbers
`claimed` with timestamps. It shows the pattern end to end:
- the mechanism (water boils cold in a vacuum, the zeolite takes the vapour, the sun resets the bed);
- the fit: the seam module's desiccant drawer, grown up, gathering about five times the water of the seam's Peltier plates;
- the honest limits: about a hundred watts averaged over a day, and a collector of a couple of square metres.

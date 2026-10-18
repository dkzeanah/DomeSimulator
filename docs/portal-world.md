# The Portal World: a RuneScape of dome know-how

`zeanahlab.com/portal`. Written 2026-10-18 from the owner's brief. This is the plan the
code is built against; each phase says what exists and what is next.

## What it is for

Anyone should be able to walk in knowing nothing and walk out understanding the geodesic
dome completely -- why the icosahedron, what frequency means, why two strut lengths, how a
log becomes wedges, how water and wind and rot kill a building and how the dome resists
them, what it costs and why. Then it becomes a real network: every member hosts a dome,
teaches what they know there, and the lessons they give and attend become a life record of
skill, validated by people who practise it.

Three layers, built in this order:

1. **The game** -- a single-player world of dome know-how: walk, talk to teachers, do quests
   that teach, fight the things that destroy buildings, collect what they drop, train skills.
2. **Your dome** -- a builder (Minecraft / Tony Hawk park editor) where each member composes
   the digital twin of their physical dome, part by part, at their username's plot.
3. **The network** -- many members in one world: visit each other's domes, attend lessons,
   collect dome-owner badges and lesson accolades, have skills certified by practitioners,
   and trade asynchronously through domes as drop-off and pickup points.

## The rules this world keeps

- **Numbers are computed, not typed** (CLAUDE.md). Every figure a teacher says, a quest
  asks or a monster's examine text states comes from the project's models through
  `website/scripts/export_facts.py`. A lesson that cannot cite its source is not shipped.
- **Each tool space is the desktop tool.** The eight gateways lead to the real tools,
  ported (the Dome Creator space is: `src/world/creator.ts`, checked against
  `dome_model.stats()` on 160 designs). A port re-uses exported tables and does only the
  tool's arithmetic in the browser, with a test against the Python.
- **Learning is the progression.** XP comes from understanding things -- reading,
  answering, building, fixing -- more than from grinding. Combat exists because buildings
  have enemies; each monster is a real failure mode and teaches its prevention.

## Systems

### Interaction (phase 1)
- Left-click walks or does the default action; **right-click** any thing for its options
  (Walk here, Examine, Talk-to, Attack, Pick-up, Enter, Read...), RuneScape-style, with the
  hover text top-left.
- **Action bar**: numbered slots (1-8) for the things you use -- eat, read the nearest lore,
  attack style, the tool of the space you are in.
- **Live shortcut list**: `?` shows every key and what it does *right now*, with what the
  thing under the cursor offers; tool spaces add their own.

### The player (phase 1)
- **Inventory** (28 slots), **skills** with the RuneScape XP curve (level 1-99), **quests**
  with journals, **badges**, **hitpoints**.
- Saved per account in D1 (`player_saves`); a guest's progress lives in their browser and is
  kept when they make an account.

### Skills
Each is a real body of dome knowledge, and each will become a path of lessons in the
network phase:

| Skill | What it is |
| --- | --- |
| Geometry | icosahedra, frequency, chord factors, strut classes, angles |
| Splitting | logs to wedges: grain, splits, yield |
| Framing | members, joints, pinwheels, raising the frame |
| Paneling | triangles closed: infill, glazing, skins |
| Foundations | pads, piers, decks, footings, hookups |
| Climate | water, condensation, seams, insulation, ventilation |
| Upkeep | defending a building against what destroys it (the combat skill) |
| Trading | costs, materials, the exchange |
| Teaching | hosting lessons for others |
| Hitpoints | how much punishment you can take |

### Teachers and quests (phase 1: the first quests)
Teachers stand in the hub and the spaces. Quests teach by doing: look at the dome, answer
from what you were told, use a tool space, bring back what a monster dropped.

### Monsters (phase 1)
Every monster is something that destroys buildings, and its examine text, its drops and
the quest that sends you after it teach how a dome resists it:

| Monster | Is really | Teaches |
| --- | --- | --- |
| Rot Grub | wood decay | keep timber dry; end grain; ventilation |
| Termite Swarm | insect attack | ground contact, piers, barriers |
| Damp Wraith | condensation | dew point, vapour, the seam channel |
| Leak Sprite | a failed seam | lapping, sealing, the seam as a gutter |
| Wind Shear | wind load | triangulation, the dome's spread load |
| Frost Heave | freeze and thaw under a footing | footings below frost, drainage |

Drops come from drop tables (always / common / uncommon / rare): building materials, coins,
food, and **lore pages** -- collectible lessons that grant XP when read.

### Combat
RuneScape ticks (0.6 s). Attack rolls accuracy against defence; hitsplats show damage;
monsters retaliate, die, drop loot on the ground, respawn. Dying sends you back to the
hilltop and keeps your items (it is a teaching world).

### Chat (phase 1)
A chatbox with tabs: Game (what happened to you), Public (members, server-backed, stored in
D1, moderated by staff). Guests read; members talk.

### Your dome: the builder (phase 2)
Each member gets a plot in the world named for their username. The builder places, moves,
rotates and removes every element of a real build -- the frame from the Dome Creator, panels
from the Panel Creator, the pad from Foundations, the cell wall, fit-out -- snapped to the
geometry, with the live bill of materials. It is the member's digital twin, saved to their
account, and the start of everything in phase 3.

### The network (phase 3)
- **Live presence**: other players visible and moving (Cloudflare Durable Objects: one per
  area, websockets; the existing ops Worker is on Workers Paid).
- **Domes that teach**: a dome's owner hosts lessons -- a timed event, in the world and/or at
  the physical dome -- and attendance is recorded.
- **Badges and accolades**: dome-owner badges for visiting (Pokemon gym style), lesson
  accolades for attending, kept for life on the member's account.
- **Certification**: practitioners of a skill validate the claims behind badges; a
  certified practitioner's validation carries weight, and is itself a record.
- **Smart domes and the exchange**: every dome is a node -- query it, leave or collect goods
  there (Grand Exchange style), and domes work together to buy and sell asynchronously.
- **Skill paths**: each skill becomes a traversable path of attendable lessons, sequenced
  from first lesson to master, so a member's record becomes a journey to mastery.

## Phases and where they stand

| Phase | What | Status |
| --- | --- | --- |
| 0 | The world, eight gateways, eight spaces | done |
| 0 | Dome Creator space is the Dome Creator | done |
| 1 | Interaction, player, inventory, skills, quests, monsters, combat, drops, chat, saves | this build |
| 1 | The other seven tools ported into their spaces | next -- one per space, each its own module (`src/world/tools/`) |
| 2 | Your dome: the builder and the digital twin | planned |
| 3 | Presence, hosted lessons, badges, certification, exchange, skill paths | planned |

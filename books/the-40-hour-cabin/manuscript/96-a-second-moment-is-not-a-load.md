---
chapter: 96
title: A Second Moment Is Not a Load
strand: reference
status: draft
target: 1050
updated: 2026-10-27
---

# 96. A Second Moment Is Not a Load

Everything in this part is geometry. Every second moment, every section modulus,
every crossover and premium was computed from a shape, and a shape is not a
strength. These numbers carry no species, no grade, no knot, no slope of grain, no
moisture, no juvenile core — the very things Chapter {{ch.grain}} and Chapter
{{ch.pith}} said decide how real wood behaves. A W32 has a larger second moment
than a two-by-four. That is true and it is not permission to span a floor with
one.

This book has a habit, by now, of saying the number that does not help. Here is
the one that does not help this part: a computed section is an argument for
building something and testing it, not a working load you can put a family under.

## From a shape to a stamp

A new structural system does not get to skip to the building and infer its
capacity afterward. It is built up from the bottom, in this order, and each step
is where a number stops being geometry and starts being evidence:

1. **The primitive.** Test individual sectors — W8 through W64 — across species,
   moisture, juvenile fraction, knot position, taper and drying history, until a
   sector has a real grade instead of a two-by-four conversion factor.
2. **The pair.** Test the dyad of Chapter {{ch.dyad}}: does opposing and
   reversing actually reduce the variation, in bending, axially and in torsion?
3. **The connection.** Measure the whole load-slip curve of each node from
   Chapter {{ch.nodes}}, not just the pounds it held — because Chapter
   {{ch.connect}}'s two limits are only limits, and the connector's stiffness is
   what sets where between them the real member lands.
4. **The recursive operators.** Build one, two, four, eight members under each
   connection strategy and measure what the stiffness ratio actually is, so the
   value of the node technology is a number rather than a hope.
5. **The components, then the design values.** Beams, columns, trusses, floors
   and shells tested as wholes, and only then the allowable stresses written down.

## The route a new system actually takes

None of that reaches a building site by itself. A genuinely new structural system
is approved as an *alternative solution*: engineering analysis, material grading,
connection and component testing, and documented performance against the code's
objectives — not a claim that a W32 is prescriptively a two-by-four. That is the
honest path, and it is a long one.

## What this part rests on

This grammar did not come from nowhere. It leans on a small body of work, each
piece cited here with the caveat its own authors put on it — and almost every one
of them says the same thing this chapter does, which is that the sections are
promising and the ratings come only from testing:

{{grammar.sources}}

That is {{grammar.sources_n}} pieces of precedent, and not one of them is a
rating. Treat this part the same way: as the reason to build the test rig, not as
the stamp at the bottom of the drawing.

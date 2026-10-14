---
chapter: 41
title: One World, Three Structures
strand: howto
status: draft
target: 1800
updated: 2026-10-14
---

# 41. One World, Three Structures

Everything in this book that can be built has a place in one 3-D world: the
pentagonal foundation of the last chapter, the wedge dome standing on it, the
wedge zome beside them, and each one's jig next to it. Open it from the
launcher (the **Wedge Zome** tab, *Open the whole world*) or with
`py -3.12 -m world3d`.

Nothing in it is drawn by hand. The foundation is the floor solver's: every
half trunk and star piece cut to the face it meets. The dome is the dome
solver's: {{world.dome}} members, each with its two end cuts. The zome is the
zome's: {{world.zome}} sticks. The world only puts them on one hilltop and lets
you take them apart.

## The layers

Down the left of the screen is the layers panel, {{world.layers}} rows: each
structure, its skin and its jig, a layer for the pieces you add yourself, and
a six-foot person for scale. Click the box to show or hide a layer; click a
layer's name to make it the one new pieces go into; right-click it to lock it,
so nothing you do can change it by accident.

Hide the dome and the zome and you have the foundation alone, with its layout
stakes and strings beside it. Show the skins and the dome is dressed and the
pentagon decked. Hide the jigs and you have the three buildings as they will
stand.

## Taking it apart

Click any piece and it reads out what it is: its name, its length in feet and
inches, its section and its board feet -- and, where the solver knows them,
its centreline and its cut length. Then:

- **Delete** takes the piece out. The structure stays standing in the world;
  whether it would stand on the hill is what the book's checks are for.
- **X, then click** saws the piece where you clicked, square to its length,
  snapped to the grid along it. You get two pieces, each closed at the cut.
- **A, then two clicks** adds a strut between two points. It snaps to the end
  of any member within a few inches, and otherwise to the grid. Choose its
  section first: **1** a wedge, **2** two wedges paired into a square, **3** a
  half trunk.
- **Arrows** move the selected piece one grid step; with **Shift** they move
  its whole layer -- that is the offset: slide the zome a foot east, raise the
  dome, nudge a jig. **Ctrl+D** copies a piece one step along.
- **[ and ]** change the grid step -- an inch up to two feet. **G** hides the
  grid.

Every change is kept as a list of steps, so **Ctrl+Z** undoes the last one
exactly, and **Ctrl+S** saves the list. The next time the world opens, the
three structures are rebuilt from their solvers and your steps are replayed
on top -- so if the dome's solver changes, your edited world changes with it.
**B** writes a cut list of everything in the world, your pieces included, to
the library.

## The three jigs

- **The foundation's jig** is its layout: a stake at every corner and every
  star crossing, string between them, laid on the ground before a log moves.
- **The dome's jig** is the dome solver's own panel jig: the table, the
  fixture and the first panel's members in their places.
- **The zome's jig** is the zome world's table, its rulers in inches and feet,
  with a row-two panel laid on it.

The world is a way to see the parts and play with them before the saw touches
a log. It is not a structural check: a strut you add, a member you delete, a
foundation you move are drawn, measured and listed, not engineered.

---
title: Every other way: what it stands on
kind: section
---

# Every other way: what it stands on

Five platforms taken off board by board, and seven priced at a rate per square metre. The two lists disagree, which is what an estimate and a take-off do; the book uses the take-off.

EVERY OTHER WAY OF DOING IT

                                               cost     weight
    Compacted gravel base                $      443              taken off, not rated: 1 lines; not a floor
    Full concrete slab                   $    2,468              taken off, not rated: 3 lines
    Framed deck on piers, sealed         $    2,916              taken off, not rated: 7 lines   <- the reference build
    Concrete ring, wood middle           $    3,039              taken off, not rated: 9 lines
    Framed deck on piers, ply and epoxy  $    4,263              taken off, not rated: 8 lines
    Grass Pad (rate)                     $       51      227 lb   $2/m2, a rate rather than a take-off
    Gravel Pad (rate)                    $      232    9,077 lb   $9/m2, a rate rather than a take-off
    Concrete Slab (rate)                 $    2,187   17,020 lb   $85/m2, a rate rather than a take-off
    Wood Deck (rate)                     $    1,544    1,589 lb   $60/m2, a rate rather than a take-off
    Stone Pavers (rate)                  $    1,415    7,375 lb   $55/m2, a rate rather than a take-off
    Treehouse Platform (rate)            $    4,889    3,971 lb   $190/m2, a rate rather than a take-off

The dearest of these is 95.0 times the cheapest. That is the size of the decision, and it is why the book states which one it assumes rather than leaving it to a reader to infer.

This book assumes framed deck on piers, sealed. Nothing else in it depends on that: change the row and the rest of the method is unchanged.

WHERE THESE NUMBERS COME FROM

pad_deck.compare() and materials.FOUNDATION_TYPES, applied to the reference build's own quantities. Nothing on this page is a rate quoted from outside the project, and nothing on it was typed: regenerate the whole table with `py -3.12 -m wedge_book.alternatives --apply`.

There is no straw-bale row and no earthbag row, because this project cannot cost one. A table with a plausible number in it that came from nowhere is worse than a table with a gap.

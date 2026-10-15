---
title: Every other way: what fills the triangles
kind: section
---

# Every other way: what fills the triangles

Sixteen panel types over 550 square feet of shell. The reference build is plywood, and the range from canvas to solar is a factor of a hundred and twenty.

EVERY OTHER WAY OF DOING IT

                               cost     weight
    Open                 $        0        0 lb   no panel at all
    Plywood              $      919      743 lb   <- the reference build
    Glass Window         $    4,852    1,689 lb   glazing
    Acrylic Window       $    3,320      676 lb   glazing
    Polycarb Twinwall    $    1,430      191 lb   glazing
    Plastic Sheeting     $       77       17 lb   glazing
    Insulated SIP        $    2,809    1,351 lb
    Shingle Panel        $    2,145    1,802 lb
    Metal Panel          $    1,532      563 lb
    Solar Panel          $    9,193    1,351 lb   190 W/m2
    Canvas               $      409       56 lb
    Hex Composite        $    2,656      957 lb
    Hex Mirror           $   10,725    1,464 lb
    Square Mirror        $    9,959    1,464 lb
    Concrete Form Panel  $    2,349    2,027 lb
    Precast Concrete     $    6,384   10,359 lb

The dearest of these is 140.0 times the cheapest. That is the size of the decision, and it is why the book states which one it assumes rather than leaving it to a reader to infer.

This book assumes plywood. Nothing else in it depends on that: change the row and the rest of the method is unchanged.

WHERE THESE NUMBERS COME FROM

materials.PANEL_TYPES, applied to the reference build's own quantities. Nothing on this page is a rate quoted from outside the project, and nothing on it was typed: regenerate the whole table with `py -3.12 -m wedge_book.alternatives --apply`.

There is no straw-bale row and no earthbag row, because this project cannot cost one. A table with a plausible number in it that came from nowhere is worse than a table with a gap.

# How This Copy Was Made

This edition was built on {{mb.built}}, in one step, by the same software that
solves the dome. Rungs one to three were written for it; rungs four to six are
routes into the two volumes; the volumes themselves were rebuilt from their own
manuscripts that day and bound in whole. Every page number in the map, the paths,
the contents, the thread pages and the index was read back from the finished
pages and printed again until none of them moved.

No figure in it was typed. Every number in the rungs is a token filled in at
build time -- from the Complete Edition's own token set, which also carries the
paperback's figures, and from a small set of this edition's own for the sizes of
the paper and straw models, each of which is the real dome scaled. An unknown token
stops the build rather than printing a blank.

The pictures are rendered by the project's software from the solved dome and from
frames of its films; none of them is a photograph. The paper dome template is
drawn from the same solved geometry, at true size.

To build another copy from the current manuscripts:

    py -3.12 -m master_book.build

It never overwrites an earlier copy: each build is a new, numbered file.

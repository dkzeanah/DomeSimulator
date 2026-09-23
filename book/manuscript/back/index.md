---
section: back
title: Index and Colophon
status: draft
target: 400
updated: 2026-09-17
---
# Index and Colophon

## Colophon

This book was not typeset from a manuscript that could drift from the
things it describes. It was built, in one step, from the same software
that draws the models and solves the geometry, and that is worth one page
of explanation because it is the book's one unusual promise.

Every figure in these pages is computed at the moment the book is built.
When a chapter says the dome is {{dome.diameter_ft}} feet across, the
number came out of the solver a second before it reached the page; when a
table prints the fold angles of {{book.chapters}} chapters' worth of
claims, each one is resolved against the geometry, and a misspelt figure
stops the build instead of printing as a blank. The arithmetic is a test
suite, and it runs before any copy of this book is allowed to exist.

The book itself is the same material in three forms: the HTML you can read
in a browser and print from, the PDF typeset from that same HTML, and the
Markdown source. All three are produced by one function, so the version
you read and the version you send cannot be different books.

The tools that made it are named in the software section, and they are
included with this book. Everything here can be regenerated, and the
declared constants can be changed -- a different tree, a different
handling limit, a different rainfall -- and the book rebuilt around them.
That is what makes this a manual rather than a memoir of one build: the
same geometry that produced this dome will produce yours.

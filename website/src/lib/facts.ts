// The project's numbers, as computed by its own models (scripts/export_facts.py). Every
// figure a page shows comes from here or from /api -- never typed into a component.
import raw from "../generated/facts.json";

export const facts = raw;
export type Tier = (typeof raw.tiers)[number];

export const cabin = raw.bookFacts.digital;
export const sample = raw.bookFacts.sample;
export const book = raw.books.find((b) => b.slug === "the-40-hour-cabin")!;
export const session = raw.books.find((b) => b.slug === "design-session");

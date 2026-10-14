import { readFileSync } from "node:fs";
import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// The page's default title, description and structured data are written at build time from
// the project's computed numbers (src/generated/facts.json), so search engines and link
// previews see the same figures the site shows -- before any script runs.
function seo(): Plugin {
  const f = JSON.parse(readFileSync(new URL("./src/generated/facts.json", import.meta.url), "utf-8"));
  const c = f.bookFacts.digital;
  const usd = (n: number) => `$${Math.round(n).toLocaleString("en-US")}`;
  const values: Record<string, string> = {
    "%SEO_TITLE%": "Zeanah Lab | Build a geodesic dome cabin from split logs",
    "%SEO_DESCRIPTION%":
      `Build a ${f.dome.acrossFt}-foot geodesic dome cabin from split logs in ${c.numbers.frameHours} hours of frame work. ` +
      `The 40 Hour Cabin: free ${f.bookFacts.sample.pages}-page sample, every cost computed, plans, and the pad network.`,
    "%SEO_JSONLD%": JSON.stringify({
      "@context": "https://schema.org",
      "@graph": [
        { "@type": "Organization", "@id": "https://www.zeanahlab.com/#org", name: "Zeanah Lab", url: "https://www.zeanahlab.com/",
          logo: "https://www.zeanahlab.com/mark.svg", founder: { "@type": "Person", name: "Donovan Zeanah" },
          sameAs: (f.site.links || []).map((l: { url: string }) => l.url) },
        { "@type": "WebSite", "@id": "https://www.zeanahlab.com/#site", name: "Zeanah Lab", url: "https://www.zeanahlab.com/",
          publisher: { "@id": "https://www.zeanahlab.com/#org" } },
        { "@type": "Book", name: c.title, alternateName: `${c.title}: ${c.subtitle}`, author: { "@type": "Person", name: c.author },
          numberOfPages: c.pages, url: "https://www.zeanahlab.com/book", image: "https://www.zeanahlab.com/img/the-40-hour-cabin-cover.jpg",
          about: ["geodesic dome", "owner-built home", "timber framing", "small house"],
          description: `A ${c.pages}-page build manual with ${c.figures} computed figures: a ${f.dome.acrossFt}-foot dome of ${f.dome.members} wedge members, ` +
            `the whole shell for ${usd(f.price.costToBuild)}.` },
      ],
    }),
  };
  return {
    name: "zeanahlab-seo",
    transformIndexHtml: (html) => Object.entries(values).reduce((h, [k, v]) => h.split(k).join(v), html),
  };
}

// `npm run dev` serves the pages alone; `npm run preview` builds and runs them with the
// API (wrangler pages dev), which is what the dev proxy below points at.
export default defineConfig({
  plugins: [react(), tailwindcss(), seo()],
  server: { proxy: { "/api": "http://127.0.0.1:8788" } },
});

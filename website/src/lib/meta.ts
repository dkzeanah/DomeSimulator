// Each page's own title and description, for search results and link previews. The words
// carry the project's computed numbers, read from facts -- never typed.

import { useEffect } from "react";

const SITE = "Zeanah Lab";
const ORIGIN = "https://www.zeanahlab.com";

function setMeta(selector: string, attr: string, key: string, value: string) {
  let el = document.head.querySelector<HTMLMetaElement | HTMLLinkElement>(selector);
  if (!el) {
    el = document.createElement(selector.startsWith("link") ? "link" : "meta") as HTMLMetaElement;
    el.setAttribute(attr, key);
    document.head.appendChild(el);
  }
  el.setAttribute(selector.startsWith("link") ? "href" : "content", value);
}

/** Title, description and canonical address for the page being shown. */
export function useMeta(title: string, description: string, path: string) {
  useEffect(() => {
    document.title = title === SITE ? title : `${title} | ${SITE}`;
    setMeta('meta[name="description"]', "name", "description", description);
    setMeta('meta[property="og:title"]', "property", "og:title", document.title);
    setMeta('meta[property="og:description"]', "property", "og:description", description);
    setMeta('meta[property="og:url"]', "property", "og:url", ORIGIN + path);
    setMeta('link[rel="canonical"]', "rel", "canonical", ORIGIN + path);
  }, [title, description, path]);
}

/** Structured data for search engines (schema.org), replaced when the page changes. */
export function useJsonLd(id: string, data: object | null) {
  useEffect(() => {
    if (!data) return;
    const el = document.createElement("script");
    el.type = "application/ld+json";
    el.id = `ld-${id}`;
    el.textContent = JSON.stringify(data);
    document.getElementById(el.id)?.remove();
    document.head.appendChild(el);
    return () => el.remove();
  }, [id, data]);
}

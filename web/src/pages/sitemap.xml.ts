import type { APIRoute } from "astro";
import { joinBase } from "../lib/base";

export const GET: APIRoute = ({ site }) => {
  const origin = (site ?? new URL("https://india-ate.org")).origin;
  const base = import.meta.env.BASE_URL;
  // The hosted site is a synthetic demo, so its generated record pages are
  // noindex. Only the landing page is advertised until real data is ingested.
  const urls = `  <url><loc>${new URL(joinBase(base, "/"), origin)}</loc></url>`;
  const body = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`;
  return new Response(body, {
    headers: { "Content-Type": "application/xml; charset=utf-8" },
  });
};

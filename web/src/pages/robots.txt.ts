import type { APIRoute } from "astro";
import { joinBase } from "../lib/base";

export const GET: APIRoute = ({ site }) => {
  const origin = (site ?? new URL("https://india-ate.org")).origin;
  const sitemap = new URL(
    joinBase(import.meta.env.BASE_URL, "/sitemap.xml"),
    origin,
  );
  const body = `User-agent: *\nAllow: /\nSitemap: ${sitemap.href}\n`;
  return new Response(body, {
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
};

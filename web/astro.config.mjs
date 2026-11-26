import { defineConfig } from "astro/config";

function normalizeBase(value) {
  const trimmed = value.replace(/^\/+|\/+$/g, "");
  return trimmed ? `/${trimmed}/` : "/";
}

const site = (process.env.SITE_URL ?? "https://india-ate.org").replace(
  /\/+$/,
  "",
);

export default defineConfig({
  output: "static",
  site,
  base: normalizeBase(process.env.BASE_PATH ?? "/"),
});

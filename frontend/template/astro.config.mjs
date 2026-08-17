import { defineConfig } from "astro/config";

// outDir and site are the only two things the generator controls outside
// of PUBLIC_* env vars — everything else about a given clinic's page is
// read from import.meta.env inside components.
export default defineConfig({
  outDir: process.env.SITE_OUT_DIR ?? "./dist",
  site: process.env.PUBLIC_SITE_URL ?? undefined,
  output: "static",
});
#!/usr/bin/env node
import { parseArgs } from "node:util";
import { spawn } from "node:child_process";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const FRONTEND_ROOT = path.resolve(__dirname, "..");
const TEMPLATE_DIR = path.join(FRONTEND_ROOT, "template");
const SITES_DIR = path.join(FRONTEND_ROOT, "sites");
const MANIFEST_PATH = path.join(FRONTEND_ROOT, "sites", "registry.json");

function usage() {
  console.log(`
Usage:
  node scripts/generate-site.mjs --slug acme-vet --clinic-id <uuid> \\
    --key pk_live_xxx --api-url https://api.example.com \\
    [--name "Acme Vet"] [--color "#2563eb"] [--logo https://...] [--site-url https://acme-vet.example.com]

  node scripts/generate-site.mjs --from-manifest   # rebuild every site in clinics.json
`);
}

function buildOne(clinic) {
  return new Promise((resolve, reject) => {
    const outDir = path.join(SITES_DIR, clinic.slug);
    const env = {
      ...process.env,
      SITE_OUT_DIR: outDir,
      PUBLIC_CLINIC_ID: clinic.clinicId,
      PUBLIC_CLINIC_SLUG: clinic.slug,
      PUBLIC_CLINIC_NAME: clinic.name ?? clinic.slug,
      PUBLIC_CLINIC_KEY: clinic.key,
      PUBLIC_API_BASE_URL: clinic.apiUrl,
      ...(clinic.color ? { PUBLIC_PRIMARY_COLOR: clinic.color } : {}),
      ...(clinic.logo ? { PUBLIC_LOGO_URL: clinic.logo } : {}),
      ...(clinic.siteUrl ? { PUBLIC_SITE_URL: clinic.siteUrl } : {}),
    };

    console.log(`\n▶ building "${clinic.slug}" → ${path.relative(FRONTEND_ROOT, outDir)}`);

    const proc = spawn("npx", ["astro", "build"], {
      cwd: TEMPLATE_DIR,
      env,
      stdio: "inherit",
      shell: process.platform === "win32",
    });

    proc.on("exit", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`astro build failed for "${clinic.slug}" (exit ${code})`));
    });
  });
}

async function updateManifest(clinic) {
  await mkdir(SITES_DIR, { recursive: true });
  let manifest = {};
  try {
    manifest = JSON.parse(await readFile(MANIFEST_PATH, "utf-8"));
  } catch {
    // no manifest yet, start fresh
  }
  manifest[clinic.slug] = { ...clinic, lastBuiltAt: new Date().toISOString() };
  await writeFile(MANIFEST_PATH, JSON.stringify(manifest, null, 2) + "\n");
}

async function main() {
  const { values } = parseArgs({
    options: {
      slug: { type: "string" },
      "clinic-id": { type: "string" },
      key: { type: "string" },
      "api-url": { type: "string" },
      name: { type: "string" },
      color: { type: "string" },
      logo: { type: "string" },
      "site-url": { type: "string" },
      "from-manifest": { type: "boolean", default: false },
      help: { type: "boolean", default: false },
    },
  });

  if (values.help) return usage();

  if (values["from-manifest"]) {
    const manifestFile = path.join(FRONTEND_ROOT, "clinics.json");
    const clinics = JSON.parse(await readFile(manifestFile, "utf-8"));
    for (const clinic of clinics) {
      await buildOne(clinic);
      await updateManifest(clinic);
    }
    console.log(`\n✓ rebuilt ${clinics.length} site(s)`);
    return;
  }

  const required = ["slug", "clinic-id", "key", "api-url"];
  const missing = required.filter((k) => !values[k]);
  if (missing.length) {
    console.error(`Missing required flag(s): ${missing.join(", ")}`);
    usage();
    process.exit(1);
  }

  const clinic = {
    slug: values.slug,
    clinicId: values["clinic-id"],
    key: values.key,
    apiUrl: values["api-url"],
    name: values.name,
    color: values.color,
    logo: values.logo,
    siteUrl: values["site-url"],
  };

  await buildOne(clinic);
  await updateManifest(clinic);
  console.log(`\n✓ done — static site at frontend/sites/${clinic.slug}/`);
}

main().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
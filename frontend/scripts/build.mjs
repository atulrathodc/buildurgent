#!/usr/bin/env node
/**
 * BuildUrgent frontend "build" step.
 *
 * buildurgent.com is a zero-dependency static site: `index.html` + `assets/` are
 * served verbatim by `../server.py`, so there is nothing to bundle, transpile or
 * copy. This script therefore VERIFIES the bundle is shippable instead of
 * rewriting it: every local `href` / `src` referenced by `index.html` (plus the
 * well-known root documents `manifest.json` and `robots.txt`) must exist on disk
 * next to the page. That catches the class of breakage a static site actually
 * suffers from — a renamed or deleted asset that silently 404s in production.
 *
 * Usage:
 *   node scripts/build.mjs            # verify (exit 1 when a reference is missing)
 *   node scripts/build.mjs --strict   # also fail on a reference to a directory
 *
 * Standard library only, no network access, no node_modules.
 */

import { existsSync, readFileSync, statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

/** The frontend root is the parent of `scripts/`. */
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const INDEX = join(ROOT, "index.html");

/** Root documents that are not referenced as attributes but must ship. */
const WELL_KNOWN = ["manifest.json", "robots.txt"];

/** Absolute/external schemes: never resolved against the document root. */
const FOREIGN = /^(?:https?:|\/\/|#|mailto:|data:|tel:|javascript:|about:|file:)/i;

const STRICT = process.argv.slice(2).includes("--strict");

/** Local (same-origin) path references in the page, normalised and de-duplicated. */
function localRefs(html) {
  const attr = /(?:href|src)\s*=\s*(?:"([^"]*)"|'([^']*)')/gi;
  const refs = new Set();
  let match;
  while ((match = attr.exec(html)) !== null) {
    const raw = (match[1] ?? match[2] ?? "").trim();
    if (!raw || FOREIGN.test(raw)) continue;
    // Drop ?query / #fragment, then make the path root-relative to this directory
    // (`/favicon.ico` -> `favicon.ico`), because the frontend IS the document root.
    const rel = raw.replace(/[?#].*$/, "").replace(/^\/+/, "");
    if (rel) refs.add(rel);
  }
  return [...refs].sort();
}

/** "missing" when the reference resolves to nothing (or, in --strict, to a directory). */
function status(rel) {
  const abs = join(ROOT, rel);
  if (!existsSync(abs)) return "missing";
  if (STRICT && statSync(abs).isDirectory()) return "missing";
  return "ok";
}

let html;
try {
  html = readFileSync(INDEX, "utf8");
} catch (err) {
  console.log(`MISSING ❌ index.html (${err.code ?? err.message})`);
  process.exit(1);
}

const refs = localRefs(html);
const missing = [...refs, ...WELL_KNOWN].filter((rel) => status(rel) === "missing");

for (const rel of missing) console.log(`MISSING ❌ ${rel}`);

if (missing.length > 0) {
  console.error(
    `build failed — ${missing.length} missing reference(s) in ${INDEX}${STRICT ? " (strict)" : ""}`
  );
  process.exit(1);
}

console.log(`OK ✅ index.html — ${refs.length} local assets resolved`);

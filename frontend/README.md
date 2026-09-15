# BuildUrgent — frontend (buildurgent.com)

The company website UI: a static, dependency-free frontend served as the document
root by `backend/server.py` (via `python3 server.py`).

## Entry point

| File | Purpose |
| --- | --- |
| `index.html` | The single-page company site: hero, about, stats, services, work, process, why-us, clients, team, FAQ and the enquiry form. |
| `assets/css/style.css` | Design-system tokens (`:root`) plus the BuildUrgent company sections (section 18). |
| `assets/css/responsive.css` | Breakpoint overrides. |
| `assets/js/` | Site behaviour: `three.min.js` + `astra3d.js` (hero WebGL background), `custom.js` (nav, cookie consent, enquiry form), `bootsnav.js`, carousel/parallax helpers. |
| `assets/images/` | `about/`, `clients/` and `portfolio/` artwork (the `portfolio/` tiles back `GET /api/projects`). |
| `manifest.json`, `robots.txt`, `Ads.txt`, `CNAME`, `favicon.ico` | Web-app manifest, crawler policy, ad-sellers file, Pages domain and icon. |

## Hard rules (pinned by `tests/test_company_site_contract.py`)

* The brand is **BuildUrgent** — in the page, `<title>`, meta description,
  Open Graph / Twitter tags, manifest, `CNAME` and `robots.txt`.
* Every `:hover` / `:focus` / `:active` rule in the company CSS block is
  **paint-only** (colour, background, border, box-shadow, opacity). The theme's
  generic `a:hover` rule is (0,1,1) and out-ranks single-class card rules, so a
  layout declaration there would re-lay-out a card the moment the pointer enters
  it. Cards are therefore `<div>` / `<article>`; only their inner links are anchors.
* The enquiry form posts **nowhere but the visitor's mail client**: it carries no
  `action` / `method`, calls `preventDefault()` and hands off to
  `mailto:hello@buildurgent.com` with the field values pre-filled.
* No personal identity ships: no personal name, email, phone, WhatsApp number,
  social handle, photo or resume PDF anywhere in the source.

## Run it

```sh
python3 server.py                 # http://0.0.0.0:8080
python3 server.py --port 9100     # custom port
```

Then open <http://127.0.0.1:9100/>. The same process serves the JSON API at
`/api/health`, `/api/profile` and `/api/projects`.

## Build

This component is a **zero-dependency static site**: there is no bundler, no
`node_modules` and no generated output. `index.html` and `assets/` are served
exactly as they sit in this folder, so the build step does not rewrite the page —
it **verifies** that the bundle is shippable.

`node scripts/build.mjs` reads `index.html`, collects every local `href` / `src`
(skipping `http(s):`, `//`, `#`, `mailto:`, `data:`, `tel:`), strips the leading
`/` and any `?query` / `#fragment`, and checks the referenced file exists here.
The root documents `manifest.json` and `robots.txt` are checked too. Each missing
file prints `MISSING ❌ <ref>` and the run exits `1`; when everything resolves it
prints `OK ✅ index.html — N local assets resolved` and exits `0`. Node's standard
library only — no network access required.

| Command | What it does |
| --- | --- |
| `npm run build` | Asset-integrity check for the static bundle; fails on a missing asset. |
| `npm run lint:html` | The same checker, exposed under the linter-style name. |
| `npm run dev` | Serve this directory on <http://127.0.0.1:9100> through `../server.py`. |
| `npm run serve` | Serve on <http://0.0.0.0:8080> through `../server.py`. |
| `npm test` | Run the repo contract tests (`python3 -m pytest ../tests -q`). |

```sh
npm run build
# OK ✅ index.html — 39 local assets resolved
```

`node scripts/build.mjs --strict` additionally fails when a reference resolves to
a directory instead of a file. Both scripts require only Node >= 18 and Python 3.

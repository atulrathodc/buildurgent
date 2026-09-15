# BuildUrgent — buildurgent.com

The company website for **BuildUrgent**, a digital product engineering studio
(web & app development, AI agents & automation, cloud/DevOps, e-commerce,
UI-UX and maintenance/support).

It is a **dependency-free static site** (`index.html` + `assets/`) served by a
small Python standard-library server that also exposes a read-only JSON API.
There is no bundler, no `package.json` and no build step.

## Run

```bash
python3 server.py --port 8111        # http://0.0.0.0:8111
```

`server.py` (repo root) is the launcher; the implementation lives in
`backend/server.py` (`PortfolioHandler`, a `SimpleHTTPRequestHandler` subclass
with sane MIME types, no-cache headers and the JSON API). Static content and the
API are served from the same process and port.

## JSON API

| Route | Purpose |
| --- | --- |
| `GET /api/health` | `{"status":"ok","service":"buildurgent-api",…}` |
| `GET /api/profile` | Company profile: name, tagline, services, contact, page title |
| `GET /api/projects` | Client case studies (tiles discovered under `assets/images/portfolio`) |
| `GET /api/` | Route listing |
| `GET /privacy-policy`, `/terms-conditions` | 302 to the PDFs in `assets/download` |

## Site sections (`index.html`)

Hero → about → stats → services → work (case studies) → process → why us →
clients (3-D coverflow carousel + testimonials) → team → FAQ → contact form →
footer. Navigation and section IDs: `#welcome-hero`, `#about`, `#services`,
`#portfolio`, `#process`, `#why-us`, `#clients`, `#team`, `#faq`, `#contact`.

The enquiry form is static: it validates in the browser and hands the brief to
the visitor's mail client (`hello@buildurgent.com`). It never posts to a
third-party endpoint.

## Assets

- `assets/css/style.css` — the whole design system (Midnight Aurora tokens in
  `:root`, Space Grotesk display + Inter body). Section 18 holds the BuildUrgent
  company sections.
- `assets/css/responsive.css`, `assets/css/parallax3d.css` — responsive and 3-D
  background layers.
- `assets/js/` — vendored jQuery/Bootstrap/Owl plus `custom.js` (sticky nav,
  smooth scroll, scrollspy, `clients3D` coverflow) and the 3-D background
  (`three.min.js` + `astra3d.js` deferred, `parallax3d.js` CSS fallback).
- `assets/download/` — `PrivacyPolicy.pdf` and `TermsConditions.pdf` (linked from
  the cookie banner and the footer).

## CSS rule for interaction states

`:hover` / `:focus` / `:active` must stay **paint-only** (colour, background,
border, box-shadow, opacity). The theme's generic `a:hover` rule is (0,1,1) and
out-ranks single-class card rules, so a layout declaration there re-lays-out a
card as soon as the pointer enters it.

## Tests

```bash
python3 -m pytest tests -q
```

- `tests/test_hero_animation_contract.py` — the hero headline is static,
  semantic `h2.hero-title` text (no animation layers, deferred background
  scripts).
- `tests/test_company_site_contract.py` — pins the BuildUrgent conversion:
  branding, required sections, SEO metadata, and the absence of every personal
  remnant of the previous portfolio.

#!/usr/bin/env python3
"""BuildUrgent runtime entry point: static site server + read-only JSON API.

buildurgent.com is a purely static site (``index.html`` + ``assets/``) plus this
small REST API that exposes the company's own data (company profile, case
studies, health). Everything is implemented with the Python standard library -
no dependencies, no build step, and nothing is injected into the published page.

Usage:
    python3 server.py                 # http://0.0.0.0:8080
    python3 server.py --port 8149     # custom port
    PORT=8149 HOST=127.0.0.1 python3 server.py

API:
    GET /api/health     -> {"status": "ok", ...}
    GET /api/profile    -> company profile (name/tagline/services/contact)
    GET /api/projects   -> client case studies discovered under assets/images

Documents:
    GET /privacy-policy    -> 302 to assets/download/PrivacyPolicy.pdf
    GET /terms-conditions  -> 302 to assets/download/TermsConditions.pdf
"""

from __future__ import annotations

import argparse
import http.server
import json
import os
import re
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
# backend/server.py -> repo root; a root-level copy of this module is the root itself.
ROOT = os.path.dirname(_HERE) if os.path.basename(_HERE) == "backend" else _HERE

#: The frontend UI is its own component: ``frontend/index.html`` plus
#: ``frontend/assets/``. It is served as the document root, so the API and the
#: published page stay in one process while the UI source tree stands alone.
#: ``ROOT`` is kept for the API's data files (index.html <title>, portfolio images).
FRONTEND = os.path.join(ROOT, "frontend")
DOCROOT = FRONTEND if os.path.isdir(FRONTEND) else ROOT

API_PREFIX = "/api/"
#: Service identifier reported by GET /api/health (renamed from "portfolio-api"
#: when the site became the buildurgent.com company site).
SERVICE_NAME = "buildurgent-api"
#: Bumped whenever the JSON API contract changes (routes added/removed, payload keys
#: renamed). Exposed by GET /api/health so consumers can pin against a known contract.
API_VERSION = "1.0"
PROJECT_DIR = os.path.join(DOCROOT, "assets", "images", "portfolio")
STARTED_AT = time.time()

#: The company the site and this API describe.
COMPANY = "BuildUrgent"

SERVICES = [
    {
        "id": "web-app-development",
        "name": "Web & App Development",
        "summary": (
            "Customer portals, internal tools and product web apps in React, Next.js, "
            "Angular, Node and Python, plus companion mobile apps in React Native and Flutter."
        ),
    },
    {
        "id": "ai-agents-automation",
        "name": "AI Agents & Automation",
        "summary": (
            "LLM agents, retrieval search over your own documents and workflow automation "
            "wired into the tools your team already runs."
        ),
    },
    {
        "id": "cloud-devops-platform",
        "name": "Cloud, DevOps & Platform",
        "summary": (
            "AWS, Azure and GCP architecture, infrastructure as code, CI/CD, Kubernetes, "
            "observability and cloud cost control."
        ),
    },
    {
        "id": "ecommerce-commerce-systems",
        "name": "E-commerce & Commerce Systems",
        "summary": (
            "B2B and B2C commerce builds, checkout and payments, loyalty, referral, "
            "personalisation and ERP / SAP Commerce / Shopify integrations."
        ),
    },
    {
        "id": "ui-ux-design-systems",
        "name": "UI-UX & Design Systems",
        "summary": (
            "Product discovery, prototyping, usability testing and accessible design "
            "systems that stay consistent as the team grows."
        ),
    },
    {
        "id": "maintenance-support",
        "name": "Maintenance & Support",
        "summary": (
            "SLA-backed support, performance rescue, security patching and legacy "
            "modernisation."
        ),
    },
]

PROFILE = {
    "name": COMPANY,
    "legal_name": COMPANY + " Technologies",
    "role": "Digital Product Engineering Studio",
    "tagline": "We build the software your business cannot wait for.",
    "description": (
        "Senior-only engineering squads for web, mobile, AI automation, cloud and "
        "commerce. Fixed scope, weekly demos, launch in weeks."
    ),
    "site": "https://buildurgent.com/",
    "contact": {
        "email": "hello@buildurgent.com",
        "sales_email": "sales@buildurgent.com",
        "support_email": "support@buildurgent.com",
        "website": "https://buildurgent.com/",
        "hours": "Mon-Fri 09:00-19:00 (UTC+5:30)",
    },
    "social": [
        "https://www.linkedin.com/company/buildurgent",
        "https://x.com/buildurgent",
        "https://github.com/buildurgent",
    ],
}

#: Case-study captions for the tile artwork shipped in assets/images/portfolio.
#: Keyed by the image stem (``p4`` for ``p4.svg``); unknown tiles fall back to
#: DEFAULT_CASE_STUDY so a newly dropped image still returns a branded record.
CASE_STUDIES = {
    "p1": ("Interactive product launch campaign", "Retail · 3D web"),
    "p2": ("Creative ad platform & asset pipeline", "Advertising · Automation"),
    "p3": ("Branded playable-ad engine", "Gaming & media · JavaScript"),
    "p4": ("Visual commerce for global retail", "Fashion & home · Headless commerce"),
    "p5": ("Ratings & reviews platform", "Parts & appliances · Integrations"),
    "p6": ("Referral & loyalty programme", "Retail · Personalisation"),
    "p7": ("Campaign attribution system", "Beauty & retail · Analytics"),
    "p8": ("Enterprise dealer locator", "Industrial · Geo search"),
    "p9": ("Rules-based product configurator", "Manufacturing · Rules engine"),
    "p10": ("Clinical access portal", "Healthcare · Compliance"),
    "p11": ("B2B commerce replatform", "Energy distribution · SAP Commerce"),
    "p12": ("Student self-service portal", "Higher education · Payments"),
    "p13": ("Field service mobile app", "Industrial · React Native"),
    "p14": ("IoT telemetry dashboard", "Manufacturing · Time series"),
    "p15": ("AI document intake agent", "Logistics · LLM automation"),
    "p16": ("Subscription billing platform", "SaaS · Payments"),
    "p17": ("Legacy platform modernisation", "Insurance · Migration"),
    "p18": ("Warehouse operations console", "Distribution · Offline & barcode"),
}

DEFAULT_CASE_STUDY = (COMPANY + " client programme", "Digital product engineering")

#: Vector tiles win over their raster twins when both ship in the same folder.
IMAGE_PRIORITY = (".svg", ".webp", ".png", ".jpg", ".jpeg")

_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def _natural_key(name: str):
    """Sort p2.svg before p10.svg."""
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", name)]


def page_title() -> str:
    """Read the <title> straight from index.html so the API never drifts from the page."""
    try:
        with open(os.path.join(ROOT, "index.html"), encoding="utf-8", errors="replace") as fh:
            match = _TITLE_RE.search(fh.read())
        if match:
            return " ".join(match.group(1).split())
    except OSError:
        pass
    return ""


def projects():
    """Case-study cards = the images actually shipped in assets/images/portfolio.

    Raster/vector twins of the same tile (``p4.svg`` + ``p4.jpg``) collapse into a
    single record, preferring the vector artwork, and each record carries the
    BuildUrgent case-study caption from :data:`CASE_STUDIES`.
    """
    try:
        names = [n for n in os.listdir(PROJECT_DIR) if not n.startswith(".")]
    except OSError:
        return []

    tiles = {}
    for name in sorted(names, key=_natural_key):
        stem, ext = os.path.splitext(name)
        ext = ext.lower()
        current = tiles.get(stem)
        rank = IMAGE_PRIORITY.index(ext) if ext in IMAGE_PRIORITY else len(IMAGE_PRIORITY)
        if current is not None and current[0] <= rank:
            continue
        title, meta = CASE_STUDIES.get(stem, DEFAULT_CASE_STUDY)
        tiles[stem] = (rank, name, title, meta)

    return [
        {
            "id": stem,
            "title": title,
            "client_type": meta,
            "image": "assets/images/portfolio/" + name,
            "url": "#portfolio",
        }
        for stem, (_rank, name, title, meta) in sorted(
            tiles.items(), key=lambda item: _natural_key(item[0])
        )
    ]


def profile():
    """Company profile served at /api/profile (name, tagline, services, contact)."""
    data = dict(PROFILE)
    data["title"] = page_title()
    data["services"] = [service["name"] for service in SERVICES]
    data["services_detail"] = [dict(service) for service in SERVICES]
    data["project_count"] = len(projects())
    return data


def health():
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "company": COMPANY,
        "api_version": API_VERSION,
        "uptime_seconds": round(time.time() - STARTED_AT, 3),
        "routes": sorted(PortfolioHandler.ROUTES),
    }


class PortfolioHandler(http.server.SimpleHTTPRequestHandler):
    """Serves the repository root with sane MIME types, no caching, and the JSON API."""

    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".css": "text/css; charset=utf-8",
        ".js": "application/javascript; charset=utf-8",
        ".mjs": "application/javascript; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".svg": "image/svg+xml",
        ".webmanifest": "application/manifest+json; charset=utf-8",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
        ".ttf": "font/ttf",
        ".eot": "application/vnd.ms-fontobject",
    }

    server_version = "BuildUrgentHTTP/1.0"
    # HTTP/1.1 keep-alive: safe because every response path (static file, JSON API,
    # redirect) sets Content-Length, and it keeps strict HTTP/1.1-only clients happy.
    protocol_version = "HTTP/1.1"

    ROUTES = {
        "/api/health": staticmethod(health),
        "/api/profile": staticmethod(profile),
        "/api/projects": staticmethod(projects),
    }

    # Legacy / bookmarkable document URLs that must not 404 on the live server.
    REDIRECTS = {
        "/privacy-policy": "assets/download/PrivacyPolicy.pdf",
        "/terms-conditions": "assets/download/TermsConditions.pdf",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DOCROOT, **kwargs)

    # ---------- API ----------
    def _api_payload(self):
        """(status, payload) for the request path, or None when it is not an API route."""
        path = self.path.split("?", 1)[0].split("#", 1)[0].rstrip("/") or "/"
        if path == "/api":
            return 200, {"service": SERVICE_NAME, "routes": sorted(self.ROUTES)}
        if not (path + "/").startswith(API_PREFIX):
            return None
        handler = self.ROUTES.get(path)
        if handler is None:
            return 404, {"error": "not_found", "path": path, "routes": sorted(self.ROUTES)}
        return 200, handler()

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _maybe_api(self) -> bool:
        resolved = self._api_payload()
        if resolved is None:
            return False
        self._send_json(*resolved)
        return True

    def _maybe_redirect(self) -> bool:
        """Serve REDIRECTS (e.g. /privacy-policy) as a 302 onto the real document."""
        path = self.path.split("?", 1)[0].split("#", 1)[0].rstrip("/") or "/"
        target = self.REDIRECTS.get(path)
        if target is None:
            return False
        self.send_response(302)
        self.send_header("Location", "/" + target)
        self.send_header("Content-Length", "0")
        self.end_headers()
        return True

    def do_GET(self):  # noqa: N802 (stdlib naming)
        if self._maybe_redirect() or self._maybe_api():
            return
        super().do_GET()

    def do_HEAD(self):  # noqa: N802 (stdlib naming)
        if self._maybe_redirect() or self._maybe_api():
            return
        super().do_HEAD()

    # ---------- headers / logging ----------
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), fmt % args))
        sys.stderr.flush()


def build_server(host: str, port: int):
    """Returns a configured ThreadingHTTPServer for the portfolio root."""
    http.server.ThreadingHTTPServer.allow_reuse_address = True
    return http.server.ThreadingHTTPServer((host, port), PortfolioHandler)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Serve the portfolio static site and API.")
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    args = parser.parse_args(argv)

    with build_server(args.host, args.port) as httpd:
        print("buildurgent server on http://%s:%d  (docroot: %s)" % (args.host, args.port, DOCROOT), flush=True)
        print("api: http://%s:%d/api/health" % (args.host, args.port), flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nshutting down", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Company-site contract tests: buildurgent.com must stay a company website.

This repository used to be a personal developer portfolio. These tests pin the
conversion so the personal remnants cannot creep back in:

* the BuildUrgent brand is in the page, its ``<title>``, the meta description,
  the Open Graph / Twitter tags, ``manifest.json``, ``CNAME``, ``robots.txt``
  and the JSON API,
* every company section exists (about, services, work, process, why us, clients,
  team, FAQ, contact) with the company offerings and channels spelled out,
* the enquiry form is live and posts nowhere but the visitor's mail client,
* no personal identity survives anywhere in the shipped source: no personal
  name / email / phone / WhatsApp number / social handles, no personal photo and
  no link to the personal resume PDF,
* the legal PDFs (``PrivacyPolicy.pdf`` / ``TermsConditions.pdf``) are still
  linked, so the cookie-consent banner keeps working,
* the new company CSS keeps every ``:hover``/``:focus``/``:active`` rule
  paint-only (the known "card re-layouts on hover" bug in this repo).

Pure text assertions (no browser, no server), mirroring
``tests/test_hero_animation_contract.py``.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INDEX_HTML = ROOT / "index.html"
STYLE_CSS = ROOT / "assets" / "css" / "style.css"
BACKEND = ROOT / "backend" / "server.py"
LAUNCHER = ROOT / "server.py"
MANIFEST = ROOT / "manifest.json"
CNAME = ROOT / "CNAME"
ROBOTS = ROOT / "robots.txt"
ADS_TXT = ROOT / "Ads.txt"
README = ROOT / "README.md"

BRAND = "BuildUrgent"
DOMAIN = "buildurgent.com"

#: Every trace of the previous owner that must never ship again. Matched
#: case-insensitively against comment-stripped source.
PERSONAL_MARKERS = (
    "atul rathod",
    "atulrathodc",                       # personal GitHub account + email local part
    "atulrathod_fullstack_resume.pdf",   # personal CV that used to be linked twice
    "atul_rathod11",                     # personal X/Twitter handle
    "atul.rathod",                       # personal Facebook / Instagram handles
    "7263932000",                        # personal phone number (also the wa.me link)
    "atul__rathod",
    "designhunk",                        # third-party endpoint the form used to POST to
    "portfolio.buildurgent.com",         # the old personal subdomain
    "assets/images/about/profile_image",  # the personal photo in the about card
)

#: The company sections the marketing page must expose (id -> heading text).
REQUIRED_SECTIONS = {
    "welcome-hero": None,
    "about": "about buildurgent",
    "services": "services",
    "portfolio": "work",
    "process": "how we work",
    "why-us": "why buildurgent",
    "clients": "clients",
    "team": "team",
    "faq": "faq",
    "contact": "contact us",
}

#: The service lines the company sells, as authored in index.html.
REQUIRED_SERVICES = (
    "Web &amp; App Development",
    "AI Agents &amp; Automation",
    "Cloud, DevOps &amp; Platform",
    "E-commerce &amp; Commerce Systems",
    "UI-UX &amp; Design Systems",
    "Maintenance &amp; Support",
)

#: Company channels that must be reachable from the contact section / footer.
REQUIRED_CHANNELS = (
    "hello@buildurgent.com",
    "sales@buildurgent.com",
    "support@buildurgent.com",
    "www.buildurgent.com",
)

#: Legal documents the cookie banner and the footer link to.
LEGAL_DOCS = ("assets/download/PrivacyPolicy.pdf", "assets/download/TermsConditions.pdf")

#: Layout properties an interaction state may never declare (see the repo skill:
#: the theme's generic `a:hover` rule is (0,1,1) and out-ranks single-class card
#: rules, so a layout declaration there re-lays-out the card on hover).
LAYOUT_PROPS = re.compile(
    r"(?:^|[;\s])(display|flex|flex-direction|flex-wrap|align-items|align-self|"
    r"justify-content|gap|row-gap|column-gap|grid|grid-template[^:]*|order|width|"
    r"min-width|max-width|height|min-height|max-height|position|top|right|bottom|"
    r"left|inset|margin[a-z-]*|padding[a-z-]*|transform|translate|scale|"
    r"letter-spacing|font-size|line-height|overflow|float|z-index)\s*:"
)

SOURCE_SUFFIXES = {
    ".html",
    ".css",
    ".js",
    ".mjs",
    ".json",
    ".py",
    ".md",
    ".txt",
    ".svg",
    ".webmanifest",
    ".xml",
}
IGNORED_DIRS = {".git", "node_modules", "__pycache__", ".mini"}

#: Marker for the BuildUrgent company CSS block at the end of style.css.
COMPANY_CSS_MARKER = "18. BuildUrgent company sections"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _strip_comments(text: str) -> str:
    """Drop CSS, HTML and Python comments (their prose may name the old owner)."""
    text = re.sub(r"/\*[\s\S]*?\*/", " ", text)
    text = re.sub(r"<!--[\s\S]*?-->", " ", text)
    return re.sub(r"(?m)^\s*#.*$", " ", text)


def _personal_offenders(path: Path) -> list:
    """Personal markers left in *path*'s live (comment-stripped) content."""
    current = Path(__file__).resolve()
    if path.resolve() == current:
        return []  # this test names the markers on purpose
    try:
        parts = set(path.relative_to(ROOT).parts)
    except ValueError:  # pragma: no cover - defensive
        return []
    if parts & IGNORED_DIRS:
        return []
    if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
        return []
    body = _strip_comments(_read(path)).lower()
    return [marker for marker in PERSONAL_MARKERS if marker in body]


def _source_files():
    for path in sorted(ROOT.rglob("*")):
        if path.is_file() and path.suffix.lower() in SOURCE_SUFFIXES:
            yield path


# --------------------------------------------------------------------------- #
# branding + SEO
# --------------------------------------------------------------------------- #
def test_brand_is_present_in_the_page():
    html = _read(INDEX_HTML)

    assert BRAND in html, "index.html must carry the BuildUrgent brand name"
    assert 'class="navbar-brand" href="index.html">%s</a>' % BRAND in html, (
        "the site header must brand the site as BuildUrgent"
    )


def test_title_and_meta_description_are_branded():
    html = _read(INDEX_HTML)
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    description = re.search(
        r'<meta\s+name="description"\s+content="([^"]*)"', html, re.IGNORECASE
    )

    assert title, "index.html must keep a <title>"
    assert BRAND in title.group(1), "the <title> must name BuildUrgent"
    assert description, "index.html must keep a meta description"
    assert BRAND in description.group(1), (
        "the meta description must name BuildUrgent (got %r)" % description.group(1)
    )


def test_open_graph_and_canonical_target_the_company_domain():
    html = _read(INDEX_HTML)

    for prop in ("og:title", "og:description", "og:url", "og:site_name"):
        match = re.search(r'<meta\s+property="%s"\s+content="([^"]*)"' % prop, html)
        assert match, "index.html must keep the %s Open Graph tag" % prop
        assert BRAND in match.group(1) or DOMAIN in match.group(1), (
            "%s must be BuildUrgent branded (got %r)" % (prop, match.group(1))
        )
    canonical = re.search(r'<link\s+rel="canonical"\s+href="([^"]*)"', html)
    assert canonical, "index.html must declare a canonical URL"
    assert canonical.group(1).startswith("https://" + DOMAIN), (
        "the canonical URL must be on %s (got %r)" % (DOMAIN, canonical.group(1))
    )


# --------------------------------------------------------------------------- #
# the company sections
# --------------------------------------------------------------------------- #
def test_required_company_sections_exist():
    html = _read(INDEX_HTML)

    for section_id in REQUIRED_SECTIONS:
        assert re.search(r'id="%s"' % re.escape(section_id), html), (
            "index.html must keep the #%s section" % section_id
        )

    missing = []
    for section_id, heading in REQUIRED_SECTIONS.items():
        if heading is None:
            continue
        if not re.search(r"<h2[^>]*>\s*" + re.escape(heading), html, re.IGNORECASE):
            missing.append("#%s (heading %r)" % (section_id, heading))
    assert not missing, "missing company section heading(s): %s" % ", ".join(missing)


def test_services_section_lists_the_company_offerings():
    html = _read(INDEX_HTML)

    for service in REQUIRED_SERVICES:
        assert service in html, "the services section must offer %r" % service
    # the old personal skill bars must not be back as "skills"
    assert 'id="skills"' not in html, (
        "the personal resume skill bars must be gone (no #skills section)"
    )


def test_contact_section_has_company_channels_and_a_live_form():
    html = _read(INDEX_HTML)

    for channel in REQUIRED_CHANNELS:
        assert channel in html, "the contact section must expose %s" % channel
    assert 'id="bu-enquiry-form"' in html, "the contact section must keep a form"
    assert re.search(r'<button[^>]*class="contact-btn"[^>]*type="submit"', html), (
        "the enquiry form must submit with a real <button type=\"submit\">"
    )
    # the form is a static-site form: it must never POST to a third party
    assert "fetch(" not in html, "the enquiry form must not fetch a third-party endpoint"
    assert ".contact-form {\n    display: block !important;\n}" in _read(STYLE_CSS), (
        "style.css must un-hide the enquiry form (the theme hid it)"
    )


def test_legal_documents_are_still_linked():
    html = _read(INDEX_HTML)

    for doc in LEGAL_DOCS:
        assert doc in html, (
            "%s must stay linked (the cookie banner / footer depend on it)" % doc
        )
    assert (ROOT / "assets" / "download" / "PrivacyPolicy.pdf").is_file()
    assert (ROOT / "assets" / "download" / "TermsConditions.pdf").is_file()


# --------------------------------------------------------------------------- #
# no personal remnants
# --------------------------------------------------------------------------- #
def test_no_personal_identity_remnants_in_source():
    """Not one shipped source file may still mention the previous owner."""
    offenders = {}
    for path in _source_files():
        found = _personal_offenders(path)
        if found:
            offenders[str(path.relative_to(ROOT))] = sorted(set(found))

    assert not offenders, "personal portfolio remnants still ship: %s" % json.dumps(
        offenders, indent=2, sort_keys=True
    )


def test_personal_resume_is_not_linked_anywhere():
    html = _read(INDEX_HTML)

    assert "resume" not in html.lower(), (
        "index.html must not link a personal resume any more"
    )
    current = Path(__file__).resolve()
    offenders = []
    for path in _source_files():
        if path.resolve() == current or set(path.relative_to(ROOT).parts) & IGNORED_DIRS:
            continue  # this test names the file on purpose; tool dirs are not shipped
        for name in ("AtulRathod_Fullstack_Resume.pdf", "Resume.pdf"):
            if name in _read(path):
                offenders.append("%s -> %s" % (path.relative_to(ROOT), name))
    assert not offenders, "the personal resume is still linked by: %s" % ", ".join(offenders)


def test_backend_serves_buildurgent_company_data():
    backend = _read(BACKEND)

    assert 'COMPANY = "%s"' % BRAND in backend, (
        "backend/server.py must describe the BuildUrgent company"
    )
    assert "buildurgent-api" in backend, (
        "the health payload must report the renamed service id"
    )
    assert '"/api/health"' in backend and '"/api/profile"' in backend and (
        '"/api/projects"' in backend
    ), "the API routes must keep their names"


def test_manifest_cname_and_robots_are_branded():
    manifest = json.loads(_read(MANIFEST))

    for key in ("name", "short_name", "description"):
        assert key in manifest, "manifest.json must keep its %s" % key
        assert BRAND in manifest[key], (
            "manifest.json %s must name BuildUrgent (got %r)" % (key, manifest[key])
        )
    assert _read(CNAME).strip() == DOMAIN, "CNAME must point at %s" % DOMAIN
    assert DOMAIN in _read(ROBOTS), "robots.txt must reference %s" % DOMAIN
    assert DOMAIN in _read(ADS_TXT), "Ads.txt must reference the %s publisher domain" % DOMAIN
    assert BRAND in _read(README), "README.md must document the BuildUrgent site"
    assert BRAND in _read(LAUNCHER), "server.py must document the BuildUrgent server"


# --------------------------------------------------------------------------- #
# the new CSS keeps the repo's paint-only interaction rule
# --------------------------------------------------------------------------- #
def test_company_css_interaction_states_are_paint_only():
    """Every `:hover`/`:focus`/`:active` rule in the BuildUrgent CSS block must be
    paint-only. A layout declaration there out-ranks the single-class card rules
    and re-lays-out the card the moment the pointer enters it."""
    css = _read(STYLE_CSS)
    marker = css.find(COMPANY_CSS_MARKER)
    assert marker != -1, "style.css must keep the BuildUrgent company CSS block"
    # the marker sits *inside* the section's banner comment, so slice from that
    # comment's opening `/*` -- otherwise the opener stays outside the slice, the
    # banner (which itself names :hover/:focus) is never stripped and its prose is
    # mis-paired as the selector of the first body (`.bu-section { padding: … }`).
    start = css.rfind("/*", 0, marker)
    assert start != -1, "the BuildUrgent CSS block must open with a banner comment"
    # drop CSS comments before pairing selectors with bodies
    block = re.sub(r"/\*[\s\S]*?\*/", " ", css[start:])

    # @media blocks in this section carry no interaction states; drop them so the
    # flat selector/body pairing below cannot mis-attribute a nested body.
    flat = re.sub(r"@media[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", " ", block)
    offenders = []
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", flat):
        if not re.search(r":(hover|focus|focus-visible|active)", selector):
            continue
        for match in LAYOUT_PROPS.finditer(body):
            offenders.append(
                "%s { %s }" % (" ".join(selector.split()), match.group(1))
            )
    assert not offenders, (
        "BuildUrgent hover/focus states must stay paint-only: %s" % "; ".join(offenders)
    )

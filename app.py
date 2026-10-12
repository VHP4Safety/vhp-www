"""VHP4Safety website: a tiny Flask app that is frozen to static files for GitHub Pages.

Every page is a plain HTML file in content/ (see README.md). The URL follows the file path:

    content/index.html            ->  /
    content/about/index.html      ->  /about/
    content/news/some-item.html   ->  /news/some-item/

Folders and files starting with "_" are data (e.g. content/_social/) and are not published as pages.
"""
import html
import re
from datetime import date, datetime
from pathlib import Path

from flask import Flask, abort, render_template, render_template_string, request
from markupsafe import Markup, escape

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"

SITE_NAME = "VHP4Safety"
SITE_TAGLINE = "Towards safety assessment based on human data"
# Top menu: (label, URL). A link is highlighted for every page below its URL.
NAV = [
    ("Home", "/"),
    ("About VHP4Safety", "/about/"),
    ("News & Events", "/news/"),
    ("Explore Our Work", "/explore/"),
    ("Contact", "/contact/"),
]

app = Flask(__name__)


# --- reading content files ---------------------------------------------------------------------

class Page:
    def __init__(self, path):
        self.path = path
        text = path.read_text(encoding="utf-8")
        head, sep, body = text.partition("\n---\n")
        self.meta = {}
        if sep:
            for line in head.splitlines():
                key, colon, value = line.partition(":")
                if colon:
                    self.meta[key.strip()] = value.strip()
        else:
            body = text
        self.body = body.strip()
        rel = path.relative_to(CONTENT).with_suffix("")
        parts = list(rel.parts)
        if parts[-1] == "index":
            parts.pop()
        self.slug = "/".join(parts)
        self.url = "/" + self.slug + ("/" if self.slug else "")

    def __getitem__(self, key):
        return self.meta.get(key, "")

    @property
    def date(self):
        try:
            return date.fromisoformat(self["date"])
        except ValueError:
            return None


_cache = {}


def all_pages():
    """Every Page under content/, newest-edit aware so edits show up while running `flask run`."""
    files = sorted(CONTENT.rglob("*.html"))
    stamp = tuple((str(f), f.stat().st_mtime_ns) for f in files)
    if _cache.get("stamp") != stamp:
        _cache["stamp"] = stamp
        _cache["pages"] = [Page(f) for f in files]
    return _cache["pages"]


def routed_pages():
    return [p for p in all_pages() if not any(part.startswith("_") for part in p.path.relative_to(CONTENT).parts)]


# --- helpers usable from inside content files (set `dynamic: yes` in the page header) ----------

def fmt_date(d):
    return f"{d.day} {d.strftime('%b %Y')}" if d else ""


def cards(*sections, featured=False, tag="", category="", when="", limit=0, label=""):
    """Tiled overview of pages in one or more content folders.

    sections  folders below content/, e.g. "news", "events", "about/crew"
    featured  only pages with `featured: yes` in their header
    tag       only pages whose `tags:` contain this word
    category  only pages with this `category:`
    when      "upcoming" or "past" (compares `date:` with today, for events)
    limit     show at most this many
    label     replace the category label on every card
    """
    today = date.today()
    found = []
    for p in routed_pages():
        folder = p.slug.rsplit("/", 1)[0] if "/" in p.slug else ""
        if folder not in sections or p.path.name == "index.html" or not p.date:
            continue
        if featured and p["featured"] != "yes":
            continue
        if tag and tag.lower() not in [t.strip().lower() for t in p["tags"].split(",")]:
            continue
        if category and p["category"] != category:
            continue
        if when == "upcoming" and p.date < today:
            continue
        if when == "past" and p.date >= today:
            continue
        found.append(p)
    found.sort(key=lambda p: p.date, reverse=(when != "upcoming"))
    if limit:
        found = found[:limit]
    return Markup(render_template("cards.html", pages=found, label=label, fmt_date=fmt_date))


def social(limit=0, full=False):
    """LinkedIn posts from content/_social/, newest first."""
    posts = sorted((p for p in all_pages() if p.slug.startswith("_social/")), key=lambda p: p["date"], reverse=True)
    if limit:
        posts = posts[:limit]
    items = []
    for p in posts:
        text = p.body
        if not full:
            text = html.unescape(re.sub(r"<[^>]+>", " ", text))
            text = " ".join(text.split())
            text = Markup("<p>") + (text[:150].rsplit(" ", 1)[0] + "…" if len(text) > 150 else text) + Markup("</p>")
        else:
            text = Markup(text)
        items.append({"source": p["source"], "date": fmt_date(p.date), "url": p["url"], "text": text})
    return Markup(render_template("social.html", items=items, full=full))


# --- routes ------------------------------------------------------------------------------------

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>/")
def page(path):
    url = "/" + path + ("/" if path else "")
    match = next((p for p in routed_pages() if p.url == url), None)
    if match is None:
        abort(404)
    body = match.body
    if match["dynamic"] == "yes":
        body = render_template_string(body, cards=cards, social=social)
    layout = match["layout"] or ("home" if url == "/" else "page")
    return render_template("layout.html", page=match, body=Markup(body), layout=layout, fmt_date=fmt_date)


@app.context_processor
def site():
    return dict(site_name=SITE_NAME, tagline=SITE_TAGLINE, nav=NAV, request_path=request.path, today=date.today())


@app.after_request
def make_links_relative(response):
    """Turn "/static/x" and "/about/" into "../static/x" etc., so the site works from any base URL
    (such as https://<user>.github.io/<repo>/) without configuration."""
    if response.mimetype == "text/html":
        depth = request.path.strip("/").count("/") + 1 if request.path.strip("/") else 0
        prefix = "../" * depth or "./"
        text = response.get_data(as_text=True)
        text = re.sub(r'\b(href|src)="/(?!/)', lambda m: f'{m.group(1)}="{prefix}', text)
        response.set_data(text)
    return response


if __name__ == "__main__":
    app.run(debug=True)

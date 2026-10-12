#!/usr/bin/env python3
"""One-off importer: copy the VHP4Safety pages from sciencrew.com into content/ and static/img/.

The site is a JavaScript app, so this talks to the same JSON API the browser uses.
It only needs to be run once; afterwards the generated files in content/ are the source of truth.

    python3 tools/import_sciencrew.py
"""
import concurrent.futures as cf
import html
import http.cookiejar
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
IMG = ROOT / "static" / "img"
BASE = "https://www.sciencrew.com"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

# channel id -> (directory/path under content/, kind)
#   list    : every article becomes its own page in the directory
#   single  : the channel's one article is the page itself (written to <path>.html)
#   social  : LinkedIn posts, written to content/_social/ (data, not routed)
CHANNELS = {
    "6594": ("news", "list"),
    "6624": ("events", "list"),
    "10173": ("events", "list"),
    "9318": ("about/crew", "list"),
    "12514": ("explore/videos", "list"),
    "6595": ("about/mission", "single"),
    "6596": ("contact", "single"),
    "6621": ("about/research-lines/rl1", "single"),
    "6622": ("about/research-lines/rl2", "single"),
    "6623": ("about/research-lines/rl3", "single"),
    "9319": ("about/partners", "single"),
    "10002": ("about/consortium", "single"),
    "12512": ("explore/platform", "single"),
    "12515": ("explore/publications", "single"),
    "6597": ("_social", "social"),
}
# Channel pages whose URL other pages link to (used to rewrite sciencrew.com links).
CHANNEL_URLS = {
    "6586": "/", "6594": "/news/", "6595": "/about/", "6596": "/contact/", "6608": "/about/research-lines/",
    "9318": "/about/crew/", "9319": "/about/partners/", "10002": "/about/consortium/", "12511": "/explore/",
    "12512": "/explore/platform/", "12514": "/explore/videos/", "12515": "/explore/publications/",
    "6624": "/events/", "10173": "/events/archive/", "6597": "/social/", "9347": "/",
    "6621": "/about/research-lines/rl1/", "6622": "/about/research-lines/rl2/", "6623": "/about/research-lines/rl3/",
}
FEATURED_CHANNEL = "9347"  # the homepage "Spotlight" articles

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [("User-Agent", UA)]


def get(url, binary=False):
    data = opener.open(url, timeout=60).read()
    return data if binary else data.decode()


def post(path, payload):
    req = urllib.request.Request(f"{BASE}/api/{path}", json.dumps(payload).encode(),
                                 {"content-type": "application/json", "User-Agent": UA})
    return json.load(opener.open(req, timeout=60))["data"]


def handshake():
    get(BASE + "/")
    get(BASE + "/idi/create?")
    get(BASE + "/idi/get")


def slugify(text, fallback):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60].strip("-")
    return s or fallback


def clean_html(s):
    s = re.sub(r"</?span[^>]*>", "", s)
    s = re.sub(r'\s+(class|style|id)="[^"]*"', "", s)
    s = re.sub(r"<p>\s*(?:&nbsp;|\xa0|<br\s*/?>|\s)*</p>", "", s)
    s = s.replace("\xa0", " ")
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def img_name(url):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", urllib.parse.unquote(url.rsplit("/", 1)[-1]))


class Importer:
    def __init__(self):
        self.downloads = {}  # local rel path -> (article id, url)
        self.article_urls = {}  # article id -> local url
        self.featured_ids = set()

    def image(self, art, url, folder):
        rel = f"img/{folder}/{img_name(url)}"
        self.downloads[rel] = (art["id"], url)
        return "/static/" + rel

    def media_html(self, art, m, folder):
        if m.get("type") == "img":
            cls = " ".join(c.replace("align-", "").replace("o4c-image", "").strip() for c in m.get("class", "").split() if c != "o4c-image")
            alt = html.escape((m.get("meta") or {}).get("alt", ""), quote=True)
            return f'<img src="{self.image(art, m["url"], folder)}" alt="{alt}" class="{cls.strip()}">'
        if m.get("type") == "gallery":
            imgs = "\n".join(f'  <img src="{self.image(art, g["url"], folder)}" alt="">' for g in m["gallery"])
            return f'<div class="gallery">\n{imgs}\n</div>'
        if "video" in m.get("type", ""):
            url = html.escape(m["url"], quote=True)
            return f'<div class="video"><iframe src="{url}" allowfullscreen loading="lazy"></iframe></div>'
        return ""

    def body(self, art, folder):
        media = {m["id"]: m for m in art.get("media", []) if "id" in m}
        content = art.get("content", "")

        def sub(match):
            m = media.get(int(match.group(1)))
            return self.media_html(art, m, folder) if m else ""

        content = re.sub(r"\[imgzine:media=(\d+)\]", sub, content)
        return clean_html(content)

    def hero(self, art, folder):
        media = art.get("media", [])
        pick = next((m for m in media if m.get("featured") and m.get("type") == "img"), None)
        if pick is None:  # first inline image that is not a gallery
            pick = next((m for m in media if m.get("type") == "img"), None)
        if pick is None:
            g = next((m for m in media if m.get("type") == "gallery"), None)
            pick = g["gallery"][0] if g else None
        return self.image(art, pick["url"], folder) if pick else ""


def front_matter(fields):
    lines = []
    for k, v in fields.items():
        if v not in ("", None, False):
            lines.append(f"{k}: {str(v).replace(chr(10), ' ').strip()}")
    return "\n".join(lines) + "\n---\n"


def fmt_date(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%Y-%m-%d")


def main():
    handshake()
    imp = Importer()
    root = post("root", {})
    chans = {c["id"]: c for c in root["conf"]["channels"]} if "conf" in root else {}
    if not chans:
        sys.exit("could not read channel list")

    featured = post("timeline", {"channelId": FEATURED_CHANNEL, "sourceIds": [s["id"] for s in chans[FEATURED_CHANNEL]["sources"]], "size": 9999})
    imp.featured_ids = {a["id"] for a in featured["articles"]}

    fetched = {}
    for cid, (path, kind) in CHANNELS.items():
        ch = chans[cid]
        tl = post("timeline", {"channelId": cid, "sourceIds": [s["id"] for s in ch["sources"]], "size": 9999})
        fetched[cid] = [post("one_article", {"articleId": a["id"], "lang": "en"})["article"] for a in tl["articles"]]
        print(cid, ch["label"], len(fetched[cid]))

    # first pass: decide local URLs (an article shown in several channels is written once)
    plan = []
    seen = {}
    for cid, (path, kind) in CHANNELS.items():
        for art in fetched[cid]:
            if art["id"] in seen:
                continue
            seen[art["id"]] = cid
            if kind == "single":
                rel = path
            elif kind == "social":
                rel = f"{path}/{fmt_date(art['cdate'])}-{art['id']}"
            else:
                rel = f"{path}/{slugify(art['title'], art['id'])}"
            plan.append((cid, kind, rel, art))
            if kind != "social":
                imp.article_urls[art["id"]] = "/" + rel + ("/" if kind == "single" else "/")
    used = set()
    for i, (cid, kind, rel, art) in enumerate(plan):  # make slugs unique
        if rel in used:
            rel = f"{rel}-{art['id']}"
            plan[i] = (cid, kind, rel, art)
            imp.article_urls[art["id"]] = "/" + rel + "/"
        used.add(rel)

    def fix_links(s):
        def rep(m):
            url = html.unescape(m.group(1))
            mm = re.match(r"https?://www\.sciencrew\.com/c/(\d+)(?:/a/(\d+))?", url)
            if mm:
                if mm.group(2) and mm.group(2) in imp.article_urls:
                    return f'href="{imp.article_urls[mm.group(2)]}"'
                if mm.group(1) in CHANNEL_URLS:
                    return f'href="{CHANNEL_URLS[mm.group(1)]}"'
                print("  unresolved sciencrew link:", url)
            return m.group(0)
        return re.sub(r'href="([^"]*sciencrew\.com/c/[^"]*)"', rep, s)

    for cid, kind, rel, art in plan:
        folder = rel.split("/")[-1] if kind != "single" else rel.replace("/", "-")
        folder = folder if kind != "social" else "social"
        body = fix_links(imp.body(art, folder))
        if kind == "social":
            props = (art.get("meta") or {}).get("imgzineArticleProps", {})
            fields = {"date": fmt_date(art["cdate"]), "source": "LinkedIn VHP",
                      "url": f"https://www.linkedin.com/feed/update/{props['urn']}/" if props.get("urn") else ""}
            text = body
        elif kind == "single":
            cats = [t[5:] for t in art.get("tags", []) if t.startswith("_cat:") and t != "_cat:Uitgelicht"]
            fields = {"title": art["title"], "date": fmt_date(art["cdate"]), "category": cats[0] if cats else "",
                      "featured": "yes" if art["id"] in imp.featured_ids else "", "image": imp.hero(art, folder),
                      "summary": " ".join(art["descr"].split())[:400]}
            text = body
        else:
            meta = art.get("meta") or {}
            cats = [t[5:] for t in art.get("tags", []) if t.startswith("_cat:") and t != "_cat:Uitgelicht"]
            is_event = meta.get("cmsKind") == "event"
            fields = {
                "title": art["title"],
                "layout": "article",
                "date": fmt_date(meta["start"].replace(" ", "T") + "Z") if is_event else fmt_date(art["cdate"]),
                "end": meta["end"][:10] if is_event and meta.get("end") else "",
                "time": f"{meta['start'][11:16]}-{meta['end'][11:16]}" if is_event and meta.get("end") and meta["start"][11:16] not in ("00:00", meta["end"][11:16]) else "",
                "location": meta.get("location", "") if is_event else "",
                "category": "Event" if is_event else next((c for c in cats if c in ("News", "Meet the Crew", "Videos")), cats[0] if cats else ""),
                "tags": ", ".join(cats),
                "featured": "yes" if art["id"] in imp.featured_ids else "",
                "image": imp.hero(art, folder),
                "intro": art.get("intro", ""),
                "summary": " ".join(art["descr"].split())[:400],
                "author": "" if "@" in art.get("authorName", "") else art.get("authorName", ""),
            }
            text = body
        out = CONTENT / (rel + ".html")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(front_matter(fields) + text + "\n")

    # images
    def dl(item):
        rel, (aid, url) = item
        dest = ROOT / "static" / rel
        if dest.exists():
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        q = urllib.parse.urlencode({"art": aid, "url": url, "v": 0, "w": 1000})
        try:
            dest.write_bytes(get(f"{BASE}/media/?{q}", binary=True))
        except Exception as e:  # keep going; report at the end
            print("  image failed:", url, e)

    print(f"downloading {len(imp.downloads)} images ...")
    with cf.ThreadPoolExecutor(6) as ex:
        list(ex.map(dl, imp.downloads.items()))

    # link-preview images hosted elsewhere refuse downloads: drop the references to missing files
    for f in CONTENT.rglob("*.html"):
        text = f.read_text()
        fixed = re.sub(r"^image: /static/(\S+)\n", lambda m: m.group(0) if (ROOT / "static" / m.group(1)).exists() else "", text, flags=re.M)
        fixed = re.sub(r'<img src="/static/([^"]+)"[^>]*>\n?', lambda m: m.group(0) if (ROOT / "static" / m.group(1)).exists() else "", fixed)
        if fixed != text:
            f.write_text(fixed)

    # site-wide images (public, no auth needed)
    for name, url in {
        "logo.png": "https://storage.imgzine.com/public/432/Home+VHP+Open+Sans+paars+2.png",
        "banner.png": "https://storage.imgzine.com/public/432/VHP+bannerwebsite+(1900+x+500+px).png",
        "tile.png": "https://storage.imgzine.com/public/432/Tegel.png",
        "favicon.png": BASE + "/ics/public/432_webapp/favicons/favicon-96x96.1615196300.png",
    }.items():
        dest = IMG / "site" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(get(url, binary=True))
    print("done")


if __name__ == "__main__":
    main()

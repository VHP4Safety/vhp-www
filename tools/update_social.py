#!/usr/bin/env python3
"""Add LinkedIn posts to the social feed (content/_social/) from pages saved as .mhtml.

Save each LinkedIn post page in the browser as "Webpage, Single File" (.mhtml) into linkedin/,
then run (see ADDING_LINKEDIN_POSTS.md):

    python3 tools/update_social.py          # add the posts that are not on the site yet
    python3 tools/update_social.py --dry    # only list what would be added

Posts already in content/_social/ (same LinkedIn post id in their `url:`) are skipped.
Only the post itself is taken from the saved page: its text, its images and its date.
"""
import email
import hashlib
import html
import re
import sys
import urllib.parse
from datetime import datetime, timezone
from email import policy
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "linkedin"
SOCIAL = ROOT / "content" / "_social"
IMG = ROOT / "static" / "img" / "social"
SOURCE = "LinkedIn VHP"

URN = re.compile(r"urn:li:(share|ugcPost|activity):(\d{15,})")
IMG_EXT = {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp"}


# --- reading the .mhtml ------------------------------------------------------------------------

def read_mhtml(path):
    """Return (snapshot URL, main HTML, {resource URL: (content type, bytes)})."""
    with open(path, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)
    page, resources = None, {}
    for part in msg.walk():
        if part.is_multipart():
            continue
        data = part.get_payload(decode=True) or b""
        ctype = part.get_content_type()
        if ctype == "text/html" and page is None:
            page = data.decode(part.get_content_charset() or "utf-8", errors="replace")
        elif part.get("Content-Location"):
            resources[part["Content-Location"]] = (ctype, data)
    if page is None:
        raise ValueError("no HTML page in this file")
    return msg.get("Snapshot-Content-Location", ""), page, resources


def post_urn(snapshot_url, page, path):
    """The post's (type, id), from the page itself, the saved URL or the file name."""
    m = re.search(r"translatable-commentary-.*?(?:shareId|ugcPostId|activityId)=(\d{15,})", page)
    if m:
        kind = re.search(r"(share|ugcPost|activity)Id=" + m.group(1), page).group(1)
        return kind, m.group(1)
    for text in (snapshot_url, path.name, page):
        m = URN.search(urllib.parse.unquote(text)) or re.search(r"(share|ugcPost|activity)-(\d{15,})", text)
        if m:
            return m.group(1), m.group(2)
    raise ValueError("cannot find the LinkedIn post id")


def post_date(post_id):
    """LinkedIn post ids start with the time of posting (milliseconds, in the upper 41 bits)."""
    return datetime.fromtimestamp((int(post_id) >> 22) / 1000, timezone.utc).date()


# --- turning the post text into clean HTML -----------------------------------------------------

def real_link(href):
    """Undo LinkedIn's link wrapper (https://www.linkedin.com/safety/go/?url=...)."""
    parsed = urllib.parse.urlparse(href)
    if parsed.path.startswith("/safety/go"):
        return urllib.parse.parse_qs(parsed.query).get("url", [href])[0]
    return href


class PostText(HTMLParser):
    """Collects the text of the first post text box after `start`, with links kept."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0  # >0 while inside the text box
        self.out = []
        self.link = None  # (href, [text]) while inside a link that is kept
        self.done = False

    def handle_starttag(self, tag, attrs):
        if self.done:
            return
        a = dict(attrs)
        if not self.depth:
            if a.get("data-testid") == "expandable-text-box":
                self.depth = 1
            return
        if tag not in ("br", "img", "wbr"):
            self.depth += 1
        if tag == "br":
            self.emit("\n")
        elif tag == "a":
            href = real_link(a.get("href", ""))
            host = urllib.parse.urlparse(href).netloc
            # mentions and hashtags become plain text, other links are kept
            keep = href and not (host.endswith("linkedin.com") and ("/in/" in href or "/search/" in href or "/company/" in href))
            self.link = (href, []) if keep else None

    def handle_endtag(self, tag):
        if self.done or not self.depth:
            return
        self.depth -= 1
        if tag == "a" and self.link:
            href, text = self.link
            self.link = None
            self.out.append(f'<a href="{html.escape(href, quote=True)}">{html.escape("".join(text))}</a>')
        if not self.depth:
            self.done = True

    def handle_data(self, data):
        if self.depth and not self.done:
            self.emit(data)

    def emit(self, text):
        if self.link:
            self.link[1].append(text)
        else:
            self.out.append(text if text == "\n" else html.escape(text, quote=False))


def post_html(page):
    start = page.find('componentkey="translatable-commentary-')
    if start < 0:
        raise ValueError("cannot find the post text (was the post itself saved, not the feed?)")
    parser = PostText()
    parser.feed(page[start:])
    text = "".join(parser.out).replace("\xa0", " ")
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        raise ValueError("the post text is empty")
    return "\n".join("<p>" + "<br>\n".join(line.strip() for line in p.split("\n")) + "</p>" for p in paragraphs)


def post_images(page, resources):
    """The images attached to the post (not profile pictures or link previews), as saved in the file."""
    found, seen = [], set()
    for src in re.findall(r'<img[^>]*\ssrc="(https://media\.licdn\.com/dms/image/[^"]*/feedshare-[^"]*)"', page):
        src = html.unescape(src)
        asset = src.split("/dms/image/")[1].split("/")[1]  # the same image in several sizes shares this id
        if asset in seen or src not in resources:
            continue
        seen.add(asset)
        found.append(resources[src])
    return found


# --- main --------------------------------------------------------------------------------------

def known_ids():
    ids = set()
    for f in SOCIAL.glob("*.html"):
        m = re.search(r"^url:.*?(\d{15,})", f.read_text(encoding="utf-8"), re.M)
        if m:
            ids.add(m.group(1))
    return ids


def main():
    dry = "--dry" in sys.argv
    files = sorted(INBOX.glob("*.mhtml")) + sorted(INBOX.glob("*.mht"))
    if not files:
        print(f"no .mhtml files in {INBOX.relative_to(ROOT)}/")
        return
    known = known_ids()
    added = failed = 0
    for path in files:
        try:
            snapshot_url, page, resources = read_mhtml(path)
            kind, post_id = post_urn(snapshot_url, page, path)
            if post_id in known:
                print(f"  already on the site: {path.name}")
                continue
            date = post_date(post_id)
            body = post_html(page)
            images = post_images(page, resources)
        except Exception as e:
            print(f"  FAILED: {path.name}: {e}")
            failed += 1
            continue
        out = SOCIAL / f"{date.isoformat()}-{post_id}.html"
        print(f"  new: {out.relative_to(ROOT)} ({len(images)} image{'s' if len(images) != 1 else ''})")
        known.add(post_id)
        added += 1
        if dry:
            continue
        for ctype, data in images:
            name = hashlib.sha256(data).hexdigest() + IMG_EXT.get(ctype, ".jpg")
            IMG.mkdir(parents=True, exist_ok=True)
            (IMG / name).write_bytes(data)
            body += f'\n<img src="/static/img/social/{name}" alt="">'
        header = f"date: {date.isoformat()}\nsource: {SOURCE}\nurl: https://www.linkedin.com/feed/update/urn:li:{kind}:{post_id}/\n---\n"
        out.write_text(header + body + "\n", encoding="utf-8")
    print(f"{added} new post{'s' if added != 1 else ''}{' (dry run, nothing written)' if dry else ''}"
          + (f", {failed} failed" if failed else ""))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Rebuild content/explore/publications.html from the NWO project page of VHP4Safety.

NWO lists the outputs that the project reported (scientific articles and other output).
This script reads that list and writes it to the publications page, grouped by type and year,
newest first. The header of the page (title, date, ...) is kept; the rest is replaced.

    python3 tools/update_publications.py            # fetch the NWO page and update
    python3 tools/update_publications.py --dry      # only show what was found
    python3 tools/update_publications.py page.html  # use a saved copy of the NWO page instead
"""
import html
import re
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "content" / "explore" / "publications.html"
NWO_URL = "https://www.nwo.nl/en/projects/rzoqi84793"

# NWO section headings (in Dutch on the English page too) -> heading on our page, in this order
TYPES = {
    "Wetenschappelijk artikel": "Scientific articles",
    "Overige Output": "Other output",
}


# Corrections for mistakes in the NWO list, by exact title. Remove an entry once NWO has fixed it.
FIXES = {
    # NWO gives the DOI and pages of another paper (Béquignon et al. 2023, 10.1021/acs.jcim.3c00220)
    "WikiPathways 2024: next generation pathway database": {
        "url": "https://doi.org/10.1093/nar/gkad960",
        "pages": "pp. D679–D689",
    },
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (vhp4safety.nl publications updater)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def text(s):
    """Plain text from an HTML fragment, with whitespace collapsed."""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def parse(page):
    """Return [(NWO type, [item dict])] from the "Outputs" part of the NWO page."""
    start = page.find("<h2>Outputs</h2>")
    if start < 0:
        raise ValueError('no "Outputs" section found on the NWO page')
    end = page.find("<h2", start + 1)
    section = page[start:end if end > 0 else len(page)]
    result = []
    for kind, body in re.findall(r"<h3[^>]*>(.*?)</h3>\s*<ul>(.*?)</ul>", section, re.S):
        items = []
        for li in re.findall(r"<li>(.*?)</li>", body, re.S):
            m = re.match(r"\s*(.*?)\s*\((\d{4})\):\s*(.*)", li, re.S)
            if not m:
                print("  skipped (no year):", text(li)[:100])
                continue
            authors, year, rest = m.groups()
            link = re.search(r'<a\s[^>]*href="([^"]+)"[^>]*>(.*?)</a>', rest, re.S)
            if link:
                url, title = html.unescape(link.group(1)), text(link.group(2))
                tail = text(rest[link.end():])
            else:
                url = ""
                title, _, tail = text(rest).partition(" pp. ")
                tail = "pp. " + tail if tail else ""
            pages = re.fullmatch(r"pp\. (\S+) - (\S+)", tail)
            if pages and not pages.group(1).isdigit():  # "pp. pub - pub", "pp. na - na"
                tail = ""
            elif pages and pages.group(1) == pages.group(2):
                tail = f"p. {pages.group(1)}"
            elif pages:
                tail = f"pp. {pages.group(1)}–{pages.group(2)}"
            item = {"authors": text(authors), "year": int(year), "url": url, "title": title, "pages": tail}
            item.update(FIXES.get(title, {}))
            items.append(item)
        result.append((text(kind), items))
    if not any(items for _, items in result):
        raise ValueError("no outputs found on the NWO page; has its layout changed?")
    return result


def item_html(it):
    e = html.escape
    title = f'<a href="{e(it["url"], quote=True)}">{e(it["title"])}</a>' if it["url"] else e(it["title"])
    pages = f", {e(it['pages'])}" if it["pages"] else ""
    return f"<li>{e(it['authors'])} ({it['year']}): {title}{pages}</li>"


def body_html(sections):
    order = list(TYPES) + [k for k, _ in sections if k not in TYPES]
    by_kind = defaultdict(list)
    for kind, items in sections:
        by_kind[kind] += items
    out = [f'<p>Outputs of the VHP4Safety project as reported to NWO (project <a href="{NWO_URL}">NWA.1292.19.272</a>), newest first.</p>']
    for kind in order:
        items = by_kind.get(kind)
        if not items:
            continue
        out.append(f"<h2>{html.escape(TYPES.get(kind, kind))}</h2>")
        years = defaultdict(list)
        for it in items:  # keeps NWO's order within a year
            years[it["year"]].append(it)
        for year in sorted(years, reverse=True):
            out.append(f"<h3>{year}</h3>\n<ul>\n" + "\n".join(item_html(it) for it in years[year]) + "\n</ul>")
    return "\n\n".join(out) + "\n"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry" in sys.argv
    source = Path(args[0]).read_text(encoding="utf-8") if args else fetch(NWO_URL)
    sections = parse(source)
    for kind, items in sections:
        years = sorted({it["year"] for it in items})
        print(f"  {TYPES.get(kind, kind)}: {len(items)} ({years[0]}–{years[-1]})" if items else f"  {kind}: 0")

    old = PAGE.read_text(encoding="utf-8")
    header, sep, old_body = old.partition("\n---\n")
    if not sep:
        raise SystemExit(f"{PAGE} has no header")
    new_body = body_html(sections)
    if new_body.strip() == old_body.strip():
        print("no changes")
        return
    if dry:
        print("the page would change (dry run, nothing written)")
        return
    PAGE.write_text(header + "\n---\n" + new_body, encoding="utf-8")
    print(f"updated {PAGE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

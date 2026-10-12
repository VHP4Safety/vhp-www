#!/usr/bin/env python3
"""Add new LinkedIn posts to the social feed (content/_social/).

LinkedIn itself needs a login, so this reads the same Sciencrew channel (6597) that the
original import used. Only posts that are not in content/_social/ yet are written; run it
before `python3 freeze.py`:

    python3 tools/update_social.py          # add what is new
    python3 tools/update_social.py --dry    # only list what would be added
"""
import sys

import import_sciencrew as sc

CHANNEL = "6597"


def main():
    dry = "--dry" in sys.argv
    out_dir = sc.CONTENT / "_social"
    known = {f.stem.rsplit("-", 1)[-1] for f in out_dir.glob("*.html")}

    sc.handshake()
    chan = {c["id"]: c for c in sc.post("root", {})["conf"]["channels"]}[CHANNEL]
    timeline = sc.post("timeline", {"channelId": CHANNEL, "sourceIds": [s["id"] for s in chan["sources"]], "size": 9999})
    new = [a for a in timeline["articles"] if str(a["id"]) not in known]
    print(f"{len(timeline['articles'])} posts online, {len(new)} new")

    imp = sc.Importer()
    for stub in new:
        art = sc.post("one_article", {"articleId": stub["id"], "lang": "en"})["article"]
        date = sc.fmt_date(art["cdate"])
        print(" ", date, art["id"])
        if dry:
            continue
        props = (art.get("meta") or {}).get("imgzineArticleProps", {})
        fields = {"date": date, "source": "LinkedIn VHP",
                  "url": f"https://www.linkedin.com/feed/update/{props['urn']}/" if props.get("urn") else ""}
        body = imp.body(art, "social")
        (out_dir / f"{date}-{art['id']}.html").write_text(sc.front_matter(fields) + body + "\n")

    for rel, (aid, url) in imp.downloads.items():  # images attached to the new posts
        dest = sc.ROOT / "static" / rel
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                dest.write_bytes(sc.get(f"{sc.BASE}/media/?art={aid}&url={sc.urllib.parse.quote(url, safe='')}&v=0&w=1000", binary=True))
            except Exception as e:
                print("  image failed:", url, e)


if __name__ == "__main__":
    main()

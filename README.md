# VHP4Safety website

A static copy of the VHP4Safety pages from Sciencrew, built with Flask and published on GitHub Pages.
The Sciencrew menu is replaced by a simple top menu. Every page is one plain HTML file; styling is in one CSS file; there is no JavaScript.

## Quick start

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/flask --app app run --debug     # live preview on http://localhost:5000, edits show up on reload
.venv/bin/python freeze.py                # writes the static site to build/
```

## Where things are

| What | Where |
| --- | --- |
| Pages | `content/**/*.html` (the URL follows the file path: `content/about/crew/index.html` is `/about/crew/`) |
| Top menu, site name | top of `app.py` (`NAV`) |
| Page frame (header, footer) | `templates/layout.html` |
| Colours, tile and card layout | `static/css/style.css` (colours are variables at the top) |
| Images | `static/img/` |
| Social feed posts | `content/_social/*.html` (folders and files starting with `_` are data, not pages) |

## Editing a page

A page is a small header, a line with `---`, then HTML:

```html
title: Contact us
intro: Optional grey text under the title
---
<p>Write normal HTML here.</p>
```

Header fields: `title`, `intro`, `layout` (`page` is the default, `article` for a narrow news-style page, `home`), `dynamic: yes` (see below).
Link to other pages with absolute paths such as `<a href="/about/">`; the build turns them into relative links so the site works under any GitHub Pages address.

**Menu buttons** (square purple tiles): `<a class="tile" href="/about/">About</a>` inside `<div class="tiles">`.

**News, events, crew, videos** are one file each. Add a file in `content/news/` and it appears on the News page and, with `featured: yes`, in the home page's spotlight:

```html
title: My news item
layout: article
date: 2026-11-01
category: News
tags: News
image: /static/img/my-folder/photo.jpg
intro: Optional bold line
summary: Short text shown on the card
---
<p>The article...</p>
```

Events also take `end:`, `time:` and `location:`. Whether an event is *upcoming* or in the *archive* is decided from its `date` when the site is built (GitHub rebuilds nightly).

**Tiled overviews** use `dynamic: yes` in the header and a call in the body:

```html
{{ cards("news") }}                                  all news, newest first
{{ cards("events", when="upcoming") }}               events from today on
{{ cards("news", "about/crew", featured=True, limit=4, label="Spotlight") }}
{{ cards("news", tag="Videos") }}                    other filters: category="..."
{{ social(5) }}  /  {{ social(full=True) }}          LinkedIn posts from content/_social/
```

## Publishing

Push to the `main` branch. In the repository settings choose *Pages → Source: GitHub Actions*; `.github/workflows/pages.yml` builds with `freeze.py` and deploys `build/`.

## Origin of the content

`tools/import_sciencrew.py` made the first copy of the pages and images from sciencrew.com. It is kept for reference and is not needed to run the site;
rerunning it overwrites `content/` and `static/img/`.
Not copied: the internal login, the other (non-VHP) Sciencrew projects, search, reactions and the member profile menu.

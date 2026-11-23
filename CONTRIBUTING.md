# Contributing to the VHP4Safety website

This repository holds the public VHP4Safety website, <https://www.vhp4safety.nl/>.
It replaces the VHP4Safety pages on Sciencrew: everything that used to be done in the Sciencrew (ORTEC) editors' dashboard is now done by editing files in this repository.

## How it works, in short

- Every page is one HTML file in [`content/`](content/). The web address follows the file name:
  `content/news/my-item.html` becomes <https://www.vhp4safety.nl/news/my-item/>.
- Each file starts with a few header lines (title, date, image, ...), then a line with only `---`, then the text of the page in HTML.
- Images and other files go in [`static/`](static/).
- When a change reaches the `main` branch, GitHub rebuilds and publishes the site automatically, usually within a few minutes.
  The site is also rebuilt every night, so upcoming events move to the archive by themselves.

## Making a change

You do not need to install anything; you can work in the browser on GitHub:

1. Go to <https://github.com/VHP4Safety/vhp-www>.
2. To change a page, open its file in `content/` and click the pencil icon (*Edit this file*).
   To add a page, open the right folder (for example `content/news/`) and choose *Add file → Create new file*.
   To add images, open or create a folder in `static/img/` and choose *Add file → Upload files*.
3. Click *Commit changes*. If you have write access you can commit to `main` directly; otherwise GitHub offers to open a pull request, which a maintainer will review and merge.
4. Wait a few minutes and check the result on the website. The progress of the build is shown under the *Actions* tab.

If you prefer working on your own computer, see the [README](README.md) for a live preview (`make serve`).

## What do you want to do?

| Task | Guide |
| --- | --- |
| Add a news item to [News & Events](https://www.vhp4safety.nl/news/) | [ADDING_NEWS.md](ADDING_NEWS.md) |
| Add an event to [Upcoming Events](https://www.vhp4safety.nl/events/) (and later the [Archive](https://www.vhp4safety.nl/events/archive/)) | [ADDING_EVENTS.md](ADDING_EVENTS.md) |
| Add LinkedIn posts to the [social feed](https://www.vhp4safety.nl/social/) | [ADDING_LINKEDIN_POSTS.md](ADDING_LINKEDIN_POSTS.md) |
| Change the home page | [below](#editing-the-landing-page) |
| Change another page (About, Partners, Research Lines, Contact, ...) | edit its file in `content/`, see the table below |

### Where the pages are

| Page | File |
| --- | --- |
| Home | [`content/index.html`](content/index.html) |
| About, Our mission and vision | [`content/about/index.html`](content/about/index.html), [`content/about/mission.html`](content/about/mission.html) |
| Meet the Crew | [`content/about/crew/`](content/about/crew/) (one file per person) |
| Partners | [`content/about/partners.html`](content/about/partners.html) |
| Research Lines | [`content/about/research-lines/`](content/about/research-lines/) |
| VHP4Safety consortium | [`content/about/consortium.html`](content/about/consortium.html) |
| News & Events | [`content/news/`](content/news/) |
| Upcoming Events, Archive | [`content/events/`](content/events/) |
| Explore Our Work (platform, publications, videos) | [`content/explore/`](content/explore/) |
| Contact | [`content/contact.html`](content/contact.html) |
| Social feed | [`content/social.html`](content/social.html), posts in [`content/_social/`](content/_social/) |

The internal part of Sciencrew (login, internal agenda, social wall, communications toolkit, organisation & planning) was not moved to this website.
This is a public site: do not add internal material here.

## Editing the landing page

The home page, <https://www.vhp4safety.nl/>, is [`content/index.html`](content/index.html). From top to bottom it shows:

| Part of the home page | Where to change it |
| --- | --- |
| Top menu (Home, About VHP4Safety, ...) | the `NAV` list near the top of [`app.py`](app.py); each entry is a label and an address |
| Banner image | replace [`static/img/site/banner.png`](static/img/site/banner.png) (keep the file name) |
| Purple tiles (About VHP4Safety, News & Events, ...) | the `<div class="tiles">` block in `content/index.html` |
| Spotlight | pages marked `featured: yes`, see below |
| Social feed | LinkedIn posts in `content/_social/`, see below |
| Footer (e-mail address, LinkedIn, PeerTube, GitHub) | [`templates/layout.html`](templates/layout.html) |

### Tiles

Each tile is one line:

```html
<div class="tiles">
  <a class="tile" href="/about/">About VHP4Safety</a>
  <a class="tile" href="/news/">VHP4Safety News &amp; Events</a>
  ...
</div>
```

The text between `>` and `</a>` is the label; `href` is the page it opens.
To rename a tile, change only the label (in Sciencrew this was *Advanced → Programs → All programs → Edit → Label*).
Write `&amp;` for an `&`. Start addresses within the site with `/`, as in `/about/`.

### Spotlight

The *Spotlight* shows the four newest pages that have this line in their header:

```
featured: yes
```

This works for news items (`content/news/`), crew introductions (`content/about/crew/`) and the pages in `content/explore/`.
To put something in the spotlight, add that line to its header (this replaces the *Uitgelicht* and *Homepage* categories in Sciencrew).
To take it out, remove the line.
Pages are ordered by their `date:`, so a new featured item pushes the oldest one out.

Which folders are included and how many items are shown is set in `content/index.html`:

```html
{{ cards("news", "about/crew", "explore", featured=True, label="Spotlight", limit=4) }}
```

### Social feed

The column next to the spotlight shows the five newest LinkedIn posts, which are stored as files in `content/_social/`.
To add new posts, save them from LinkedIn and import them with `tools/update_social.py`, as described in [ADDING_LINKEDIN_POSTS.md](ADDING_LINKEDIN_POSTS.md).
To show more or fewer posts, change the number in `{{ social(5) }}` in `content/index.html`.

### Text under the banner

The `intro:` line in the header of `content/index.html` is shown under the banner, and search engines use it as the description of the site.

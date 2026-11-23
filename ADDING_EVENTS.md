# Adding an event

Events appear under [Upcoming Events](https://www.vhp4safety.nl/events/), soonest first, which you reach from [News & Events](https://www.vhp4safety.nl/news/).
Once the date has passed, an event moves to the [Archive](https://www.vhp4safety.nl/events/archive/) by itself; the site is rebuilt every night for this.
This replaces *Content → Agenda → Create new agenda item* in the Sciencrew dashboard.
See [CONTRIBUTING.md](CONTRIBUTING.md) for how to edit files on GitHub.

**Only public events belong here.** In Sciencrew, internal events went to the internal agenda (the *Calendar* category) behind the login.
That agenda was not moved to this website, so do not add internal meetings.

## Steps

1. **Add an image (optional).** Upload it to a new folder in [`static/img/`](static/img/), for example `static/img/eurotox-congress-2026/`.
   The event logo or one of the standard VHP4Safety images works well.
2. **Create the file.** Open [`content/events/`](content/events/) and choose *Add file → Create new file*.
   Name it after the event, in lowercase with hyphens and ending in `.html`, for example `eurotox-congress-2026.html`.
   The name becomes the web address: `https://www.vhp4safety.nl/events/eurotox-congress-2026/`.
3. **Fill in the header and the text** (see the example below).
4. **Commit the change** and check the event on the website after a few minutes.

## Example

```html
title: EUROTOX Congress 2026
layout: article
date: 2026-09-13
end: 2026-09-16
time: 09:00-17:00
location: Vienna, Austria
category: Event
tags: Events
image: /static/img/eurotox-congress-2026/eurotox-2026-logo.png
summary: From 13 to 16 September 2026, the 60th Congress of the European Societies of Toxicology takes place in Vienna, Austria.
---
<p>From 13 to 16 September 2026, the 60th Congress of the European Societies of Toxicology (EUROTOX 2026) will take place in Vienna, Austria.</p>

<p>More information? Please visit the <a href="https://www.eurotox2026.com/">EUROTOX 2026 website</a>.</p>
```

## The header lines

| Line | Required | Meaning |
| --- | --- | --- |
| `title:` | yes | Name of the event |
| `layout: article` | yes | Always `article` for events |
| `date:` | yes | (First) day of the event as `YYYY-MM-DD`; decides whether it is upcoming or in the archive |
| `end:` | no | Last day, for events of more than one day, as `YYYY-MM-DD` |
| `time:` | no | For example `13:00-14:30 CET` |
| `location:` | no | City and country, a venue, or `Online` |
| `category: Event` | yes | Label shown on the card and under the title |
| `tags: Events` | no | Keep `Events` (the *Events* category in Sciencrew) |
| `image:` | no | Image shown on the event card (the *featured image* in Sciencrew) |
| `summary:` | no | One or two sentences for the card and for search engines |
| `intro:` | no | Bold opening line, shown under the title and on the card |

The text after `---` is HTML, as for news items; see the table in [ADDING_NEWS.md](ADDING_NEWS.md#writing-the-text).
Include a link to the registration or the organiser's page.

## Announcing the event as news

An event does not appear in the home page *Spotlight*.
To draw attention to it there, also write a short news item with `featured: yes` that links to the event page (see [ADDING_NEWS.md](ADDING_NEWS.md)), for example `<a href="/events/eurotox-congress-2026/">EUROTOX 2026</a>`.

## After the event

Nothing needs to be done: the event moves to the archive by itself.
To share how it went, write a news item (for example "Looking back at ...") and link to it from the event page.

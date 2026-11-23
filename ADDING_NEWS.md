# Adding a news item

News items appear on [News & Events](https://www.vhp4safety.nl/news/), newest first, and, if you choose, in the *Spotlight* on the [home page](https://www.vhp4safety.nl/).
This replaces *Content → Create a new article* in the Sciencrew dashboard.
See [CONTRIBUTING.md](CONTRIBUTING.md) for how to edit files on GitHub.

## Steps

1. **Add the images.** Open [`static/img/`](static/img/) on GitHub and upload your images into a new folder named after the news item, for example `static/img/looking-back-at-estiv-2026/`.
   Use images with a good resolution: the same image is used, scaled down, on the news card.
2. **Create the file.** Open [`content/news/`](content/news/) and choose *Add file → Create new file*.
   Name it after the title, in lowercase with hyphens and ending in `.html`, for example `looking-back-at-estiv-2026.html`.
   The name becomes the web address: `https://www.vhp4safety.nl/news/looking-back-at-estiv-2026/`.
3. **Fill in the header and the text** (see the example below).
4. **Commit the change** and check the news item on the website after a few minutes.
   Images may look different on the site than you expected, so do check the published page.

## Example

```html
title: Looking Back at ESTIV 2026
layout: article
date: 2026-07-20
category: News
tags: News
image: /static/img/looking-back-at-estiv-2026/group-photo.jpg
intro: VHP4Safety shines at ESTIV 2026 and the ASPIS Open Symposium!
summary: The past month has been a whirlwind of activity for VHP4Safety, marked by a strong presence at ESTIV 2026.
---
<p>The past month has been a whirlwind of activity for VHP4Safety ...</p>

<img src="/static/img/looking-back-at-estiv-2026/group-photo.jpg" alt="The VHP4Safety team at ESTIV 2026">

<p><strong>Pre-Congress Workshop</strong></p>
<p>Our members ... More on the <a href="https://estiv.org/">ESTIV website</a>.</p>
```

## The header lines

| Line | Required | Meaning |
| --- | --- | --- |
| `title:` | yes | Title of the news item |
| `layout: article` | yes | Always `article` for news |
| `date:` | yes | Publication date as `YYYY-MM-DD`; the news page is sorted on it |
| `category: News` | yes | Label shown on the card and under the title |
| `tags: News` | no | Keep `News`; add `Videos` if the item is mainly a video |
| `image:` | no | Image shown on the news card (the *featured image* in Sciencrew) |
| `intro:` | no | Bold opening line, shown under the title and on the card |
| `summary:` | no | One or two sentences for the card and for search engines |
| `featured: yes` | no | Also show the item in the *Spotlight* on the home page (the *Uitgelicht* category in Sciencrew) |
| `author:` | no | Name shown under the title |

The `image:` is only used on the card, not at the top of the article.
As with Sciencrew, it reads better to put an image inside the text, with an `<img>` line as in the example; you can use the same image for both.

## Writing the text

The text after `---` is HTML. The most common pieces:

| You want | Write |
| --- | --- |
| A paragraph | `<p>Text</p>` |
| Bold | `<strong>bold</strong>` |
| A heading inside the article | `<h2>Heading</h2>` |
| A link | `<a href="https://example.org/">link text</a>` |
| A link to another page on the site | `<a href="/events/">upcoming events</a>` |
| A bulleted list | `<ul><li>first</li><li>second</li></ul>` |
| An image | `<img src="/static/img/my-folder/photo.jpg" alt="short description">` |

Copying an existing file in `content/news/` and changing it is often the quickest way to start.

## Attachments

To add a PDF or another file, upload it to a folder such as `static/files/my-news-item/` and link to it:
`<a href="/static/files/my-news-item/report.pdf">Read the report (PDF)</a>`.

## Changing or removing a news item

Edit the file in `content/news/` to change it. Delete the file to remove the item; delete its images in `static/img/` as well if nothing else uses them.

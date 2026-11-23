# Adding LinkedIn posts to the social feed

The home page shows the five newest posts from the [VHP4Safety LinkedIn page](https://www.linkedin.com/company/virtual-human-platform-for-safety-assessment-vhp4safety/), and the [social feed page](https://www.vhp4safety.nl/social/) shows all of them.
LinkedIn does not let other websites read its posts, so new posts are copied by hand: you save each post as a file, and a small script turns it into a page of this website.
Each post becomes one file in [`content/_social/`](content/_social/).

You need a copy of this repository on your own computer, Python 3 (nothing else to install), and Chrome or Edge.
See [CONTRIBUTING.md](CONTRIBUTING.md) for the general workflow.

## Steps

1. **Open the post on its own page.** On LinkedIn, click the time stamp of the post (for example "2 d"), or use *… → Copy link to post* and open that link.
   Save the post page, not the LinkedIn feed: the script only reads the post itself.
2. **Save the page as a single file.** Press <kbd>Ctrl</kbd>+<kbd>S</kbd> (<kbd>Cmd</kbd>+<kbd>S</kbd> on a Mac), choose *Webpage, Single File (\*.mhtml)*, and save it in the `linkedin/` folder of the repository (create the folder if it is not there).
   Any file name works. Repeat this for every new post; posts that are already on the website are skipped, so it does no harm to save one twice.
3. **Run the script** in the repository folder:

   ```sh
   python3 tools/update_social.py --dry    # shows what would be added
   python3 tools/update_social.py          # adds the new posts
   ```

   For each new post it writes `content/_social/<date>-<post id>.html`, with the date on which the post was published, and copies the images of the post to `static/img/social/`.
4. **Check the result** with a preview (`make serve`, then open <http://localhost:5000/>), or read the new files in `content/_social/`.
   You can correct the text in those files by hand, just like any other page.
5. **Commit and push** the new files in `content/_social/` and `static/img/social/`.
6. **Delete the `.mhtml` files** from `linkedin/`.

## Keep the .mhtml files out of the repository

The `linkedin/` folder is ignored by git, so the saved files cannot be committed by accident.
That matters: a saved LinkedIn page contains much more than the post, such as parts of your own LinkedIn account (your messages panel, your name and picture).
The script only takes the text, the images and the date of the post; the rest stays in the `.mhtml` file, which is why you should delete it once the post is imported.

## What the script takes from a post

| From LinkedIn | On the website |
| --- | --- |
| Text of the post | Paragraphs, with the line breaks of the original |
| Links (`https://lnkd.in/...`) | Links, without LinkedIn's "you are leaving LinkedIn" redirect |
| Mentions of people and hashtags | Plain text |
| Photos attached to the post | Images below the text |
| Preview image of a shared link (for example a YouTube video) | Not included: LinkedIn does not save it in the file |
| Comments and reactions | Not included |
| Date of the post | Worked out from the post's id, so it is always the publication date |

## When something goes wrong

- **"FAILED: ... cannot find the post text"**: the file is probably the LinkedIn feed or another page, not the post itself. Open the post on its own page (step 1) and save it again.
- **The text ends with "…more"**: LinkedIn showed a shortened text when you saved the page. Open the post on its own page, where the whole text is shown, and save it again.
- **A post with a video or a document has no image**: those are not saved in the file. Add an image or a link by hand in the new file in `content/_social/` if needed.
- **Removing a post from the website**: delete its file from `content/_social/` (and its images from `static/img/social/` if nothing else uses them).

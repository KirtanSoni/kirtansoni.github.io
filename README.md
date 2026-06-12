# Personal site

Plain static HTML + one CSS file. Blog posts are authored in **Markdown**
(Obsidian-friendly) and compiled to HTML by a small zero-dependency script.

## Files
- `content/` — **Markdown source** for every post (the single source of truth)
- `data/projects.json` — **the projects directory** (name, year, stack, desc,
  links, `featured` flag). Edit this to add/remove projects.
- `data/tools.json` — **the tools directory** (name, desc, link)
- `build.py` — compiles `content/*.md` → `posts/*.html` and regenerates
  `writing.html`, `projects.html`, `tools.html`, the home-page lists, and the
  RSS feed
- `index.html` — home / about. The Recent-writing / Selected-projects / Tools
  lists live between `<!-- POSTS|PROJECTS|TOOLS:START/END -->` markers and are
  filled in by the build — don't edit those by hand
- `writing.html`, `projects.html`, `tools.html` — *(generated — edit via
  `content/` and `data/`)*
- `posts/` — generated post HTML *(do not edit; regenerated from `content/`)*
- `style.css` — all styling, incl. light/dark themes
- `site.js` — dark-mode toggle + layout-debug guides
- `feed.xml` — RSS feed *(generated)*
- `assets/` — images (e.g. `assets/me.jpg` headshot, post screenshots)

## Add a project / tool
Append an object to `data/projects.json` (or `data/tools.json`) and run
`python3 build.py`. Project links are optional — use only ones that exist:
`repo`, `live`, `package`, `post`. `"featured": true` puts it on the home page.

## Write a post (Obsidian workflow)
1. Create a new note in `content/`, e.g. `content/my-post.md`. The filename is
   the URL slug (`posts/my-post.html`).
2. Start it with frontmatter:

   ```markdown
   ---
   title: My Post Title
   date: 2026-06-07
   description: One sentence for search results and the RSS feed.
   tags: [Python, Notes]
   subtitle: Optional line shown next to the date
   reading_time: 4 min read
   draft: false
   ---
   ```

3. Write the body in normal Markdown. Then run:

   ```
   python3 build.py
   ```

   It rebuilds every post and refreshes the lists + feed. Set `draft: true` to
   keep a note out of the build.

### Markdown supported
Headings, **bold**/*italic*, `inline code`, fenced code blocks, links, images,
blockquotes, ordered/unordered lists, and raw HTML (passes straight through).

Obsidian extras:
- `![[screenshot.png]]` → image from `assets/` (auto-hides if missing)
- `![[wide-banner.png|banner]]` → full-width banner image
- `[[other-post]]` or `[[other-post|label]]` → link to another post
- Embed a video by pasting raw HTML:
  ```html
  <div class="video">
    <iframe src="https://www.youtube.com/embed/VIDEO_ID" title="demo" allowfullscreen></iframe>
  </div>
  ```

Put image files in `assets/` and reference them as `assets/foo.png` (Obsidian
embeds resolve there automatically).

### Sidenotes (margin annotations)
Inline, inside any raw-HTML paragraph (`id` must be unique per page; the
number renders automatically):

```html
…text<span class="sn"><label class="sn-pill" for="sn-myid"></label><input
  class="sn-toggle" type="checkbox" id="sn-myid"><span class="sn-note">The
  aside text.</span></span> more text…
```

Wide screens: the note hangs in the right margin beside its anchor. Narrow
screens: tapping the numbered pill expands it inline. Pure CSS, no JS.
What belongs in a sidenote (and how to write posts at all): see `WRITEUPS.md`.

### Optional: richer Markdown
The build works with no dependencies. For fuller Markdown (tables, footnotes,
etc.) install python-markdown and it's used automatically:

    pip install markdown

## Preview locally
    python3 -m http.server 8000

Then visit http://localhost:8000 (hard-reload with Cmd+Shift+R after a rebuild).

## Dark mode & debug guides
- Theme follows the system setting; the ☾/☀ button overrides it (saved in
  `localStorage`).
- Press **`g`** (or add `#debug` to a URL) to toggle layout guide lines while
  designing. Off by default.

## RSS
`feed.xml` is generated. Set your real domain by changing `SITE_URL` near the
top of `build.py`, then rebuild.

## Publish (free options)
- **GitHub Pages**: push this folder to a repo, enable Pages on the main branch.
- **Netlify / Cloudflare Pages**: drag-and-drop the folder.

Run `python3 build.py` before publishing, and replace the placeholder
GitHub / LinkedIn / CV links in `index.html`.

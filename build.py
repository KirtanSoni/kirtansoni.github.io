#!/usr/bin/env python3
"""
Static blog builder — Markdown (Obsidian) -> HTML.

Usage:
    python3 build.py

What it does:
  * Reads every .md file in   content/
  * Converts each to          posts/<slug>.html   (slug = filename)
  * Regenerates               writing.html         (full post list)
  * Regenerates               feed.xml             (RSS)
  * Updates the "recent" list in index.html (between POSTS markers)

Dependencies: NONE required. If `python-markdown` is installed
(`pip install markdown`) it is used automatically for richer parsing;
otherwise a built-in converter handles the common subset.

Obsidian-friendly extras (work in both engines):
  ![[image.png]]          -> <img src="../assets/image.png">
  ![[image.png|banner]]   -> wide banner <img class="banner" ...>
  [[other-post]]          -> link to other-post.html
  [[other-post|label]]    -> link with custom label
  raw HTML (e.g. a <div class="video">...</div>) passes straight through.

Image paths: write them as  assets/foo.png  in Markdown; the build
rewrites them to ../assets/foo.png for the generated post.
"""

import os
import re
import html
import json
import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
POSTS = os.path.join(ROOT, "posts")
DATA = os.path.join(ROOT, "data")

SITE_TITLE = "Kirtan Soni"
SITE_EMAIL = "1kirtansoni@gmail.com"
SITE_URL = "https://kirtansoni.github.io"
RECENT_ON_HOME = 5


def load_data(name):
    """Read data/<name>.json; missing file -> empty list."""
    path = os.path.join(DATA, name + ".json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)

# ---------------------------------------------------------------- frontmatter
def parse_front_matter(text):
    """Return (meta_dict, body). Frontmatter is a leading ---\n...\n--- block."""
    meta = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            block = text[3:end].strip("\n")
            body = text[end + 4:].lstrip("\n")
            for line in block.split("\n"):
                if not line.strip() or ":" not in line:
                    continue
                key, val = line.split(":", 1)
                meta[key.strip()] = val.strip()
            return meta, body
    return meta, text


def parse_tags(raw):
    if not raw:
        return []
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]
    return [t.strip().strip("'\"") for t in raw.split(",") if t.strip()]


def unquote(s):
    s = (s or "").strip()
    if len(s) >= 2 and s[0] in "'\"" and s[-1] == s[0]:
        return s[1:-1]
    return s


# ---------------------------------------------------------------- obsidian pre-pass
def preprocess_obsidian(text):
    # ![[file|banner]]  /  ![[file]]
    def embed(m):
        inner = m.group(1)
        if "|" in inner:
            fname, opt = inner.split("|", 1)
            cls = ' class="banner"' if opt.strip().lower() == "banner" else ""
        else:
            fname, cls = inner, ""
        fname = fname.strip()
        alt = os.path.splitext(os.path.basename(fname))[0]
        return f'<img{cls} src="assets/{fname}" alt="{alt}" onerror="this.style.display=\'none\'">'
    text = re.sub(r"!\[\[([^\]]+)\]\]", embed, text)

    # standard markdown image with {.banner} attribute -> raw img (engine-agnostic)
    def banner_img(m):
        alt, src = m.group(1), m.group(2)
        return f'<img class="banner" src="{src}" alt="{alt}" onerror="this.style.display=\'none\'">'
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)\{\.banner\}", banner_img, text)

    # [[slug|label]]  /  [[slug]]
    def wikilink(m):
        inner = m.group(1)
        if "|" in inner:
            slug, label = inner.split("|", 1)
        else:
            slug = label = inner
        return f"[{label.strip()}]({slug.strip()}.html)"
    text = re.sub(r"\[\[([^\]]+)\]\]", wikilink, text)
    return text


# ---------------------------------------------------------------- markdown -> html
def convert_markdown(text):
    text = preprocess_obsidian(text)
    try:
        import markdown
        body = markdown.markdown(
            text,
            extensions=["fenced_code", "tables", "sane_lists"],
        )
    except ImportError:
        body = fallback_markdown(text)
    # fix asset paths for files living in /posts
    body = body.replace('src="assets/', 'src="../assets/')
    return body


def _inline(s):
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = re.sub(r"`([^`]+)`", lambda m: "<code>%s</code>" % m.group(1), s)
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)",
               lambda m: '<img src="%s" alt="%s">' % (m.group(2), m.group(1)), s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
               lambda m: '<a href="%s">%s</a>' % (m.group(2), m.group(1)), s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    return s


def fallback_markdown(text):
    lines = text.split("\n")
    out, i, n = [], 0, len(lines)
    while i < n:
        line = lines[i]
        if line.strip() == "":
            i += 1
            continue
        # fenced code
        if line.lstrip().startswith("```"):
            i += 1
            code = []
            while i < n and not lines[i].lstrip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            esc = html.escape("\n".join(code))
            out.append("<pre><code>%s</code></pre>" % esc)
            continue
        # raw HTML block
        if line.lstrip().startswith("<"):
            block = []
            while i < n and lines[i].strip() != "":
                block.append(lines[i])
                i += 1
            out.append("\n".join(block))
            continue
        # heading
        m = re.match(r"(#{1,6})\s+(.*)", line)
        if m:
            lvl = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (lvl, _inline(m.group(2).strip()), lvl))
            i += 1
            continue
        # horizontal rule
        if re.match(r"(-{3,}|\*{3,}|_{3,})\s*$", line.strip()):
            out.append("<hr>")
            i += 1
            continue
        # blockquote
        if line.lstrip().startswith(">"):
            quote = []
            while i < n and lines[i].lstrip().startswith(">"):
                quote.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>%s</blockquote>" % _inline(" ".join(quote)))
            continue
        # unordered list
        if re.match(r"\s*[-*+]\s+", line):
            items = []
            while i < n and re.match(r"\s*[-*+]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*+]\s+", "", lines[i]))
                i += 1
            out.append("<ul>" + "".join("<li>%s</li>" % _inline(x) for x in items) + "</ul>")
            continue
        # ordered list
        if re.match(r"\s*\d+\.\s+", line):
            items = []
            while i < n and re.match(r"\s*\d+\.\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+\.\s+", "", lines[i]))
                i += 1
            out.append("<ol>" + "".join("<li>%s</li>" % _inline(x) for x in items) + "</ol>")
            continue
        # paragraph
        para = []
        while (i < n and lines[i].strip() != ""
               and not lines[i].lstrip().startswith(("#", ">", "```", "<"))
               and not re.match(r"\s*[-*+]\s+", lines[i])
               and not re.match(r"\s*\d+\.\s+", lines[i])):
            para.append(lines[i].strip())
            i += 1
        out.append("<p>%s</p>" % _inline(" ".join(para)))
    return "\n".join(out)


# ---------------------------------------------------------------- templates
def nav(active, prefix=""):
    def cls(name):
        return ' class="active"' if name == active else ""
    return f"""  <header class="site">
    <a class="name" href="{prefix}index.html">{SITE_TITLE}</a>
    <nav>
      <a href="{prefix}index.html"{cls('home')}>Home</a>
      <a href="{prefix}writing.html"{cls('writing')}>Writing</a>
      <a href="{prefix}projects.html"{cls('projects')}>Projects</a>
      <a href="{prefix}tools.html"{cls('tools')}>Tools</a>
      <button class="theme-toggle" type="button" aria-label="Toggle theme">☾</button>
    </nav>
  </header>"""


THEME_SNIPPET = ("<script>(function(){try{var t=localStorage.getItem('theme');"
                 "if(t)document.documentElement.setAttribute('data-theme',t);}catch(e){}})();</script>")


def render_post(meta, body):
    title = unquote(meta.get("title", "Untitled"))
    desc = unquote(meta.get("description", ""))
    tags = parse_tags(meta.get("tags", ""))
    parts = []
    if meta.get("subtitle"):
        parts.append(unquote(meta["subtitle"]))
    parts.append(meta["_date_display"])
    if meta.get("reading_time"):
        parts.append(unquote(meta["reading_time"]))
    post_meta = " · ".join(parts)
    tags_html = ""
    if tags:
        tags_html = f'\n    <p class="tags">Tags: {", ".join(tags)}</p>'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} — {SITE_TITLE}</title>
  <meta name="description" content="{html.escape(desc)}">
  <link rel="stylesheet" href="../style.css">
  <link rel="alternate" type="application/rss+xml" title="{SITE_TITLE} — Writing" href="../feed.xml">
  {THEME_SNIPPET}
</head>
<body>
<div class="wrap">

{nav('writing', prefix='../')}

  <a class="back" href="../writing.html">← All writing</a>

  <article>
    <h1>{html.escape(title)}</h1>
    <p class="post-meta">{html.escape(post_meta)}</p>

{body}{tags_html}
  </article>

  <footer class="site">
    © 2026 {SITE_TITLE} · <a href="mailto:{SITE_EMAIL}">{SITE_EMAIL}</a>
  </footer>

</div>
<script src="../site.js"></script>
</body>
</html>
"""


def list_items(posts, prefix=""):
    rows = []
    for p in posts:
        rows.append(
            f'    <li>\n'
            f'      <span class="date">{p["_date_display"]}</span>\n'
            f'      <a class="title" href="{prefix}posts/{p["slug"]}.html">{html.escape(p["title"])}</a>\n'
            f'    </li>'
        )
    return "\n".join(rows)


def render_writing(posts):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Writing — {SITE_TITLE}</title>
  <meta name="description" content="Blog posts and notes by {SITE_TITLE}.">
  <link rel="stylesheet" href="style.css">
  <link rel="alternate" type="application/rss+xml" title="{SITE_TITLE} — Writing" href="feed.xml">
  {THEME_SNIPPET}
</head>
<body>
<div class="wrap">

{nav('writing')}

  <h2 class="section">Writing</h2>
  <ul class="entries">
{list_items(posts)}
  </ul>

  <p style="margin-top:24px;font-size:15px"><a href="feed.xml">RSS feed</a></p>

  <footer class="site">
    © 2026 {SITE_TITLE} · <a href="mailto:{SITE_EMAIL}">{SITE_EMAIL}</a>
  </footer>

</div>
<script src="site.js"></script>
</body>
</html>
"""


# ---------------------------------------------------------------- directory (projects & tools)
LINK_ORDER = [("live", "live"), ("repo", "source"), ("package", "package"), ("post", "writeup")]


def project_links(p):
    """' · '-joined anchors for whichever links a project actually has."""
    links = p.get("links", {})
    out = []
    for key, label in LINK_ORDER:
        if links.get(key):
            out.append(f'<a href="{html.escape(links[key])}">{label}</a>')
    return " · ".join(out)


def primary_link(p):
    links = p.get("links", {})
    for key, _ in LINK_ORDER:
        if links.get(key):
            return links[key]
    return None


def project_item(p):
    href = primary_link(p)
    title = (f'<a class="title" href="{html.escape(href)}">{html.escape(p["name"])}</a>'
             if href else f'<span class="title">{html.escape(p["name"])}</span>')
    meta = " · ".join(x for x in [p.get("year", ""), ", ".join(p.get("stack", []))] if x)
    links = project_links(p)
    links_html = f'\n      <p class="meta">{links}</p>' if links else ""
    return (f'    <li>\n'
            f'      {title}\n'
            f'      <p class="meta">{html.escape(meta)}</p>\n'
            f'      <p class="desc">{html.escape(p["desc"])}</p>{links_html}\n'
            f'    </li>')


def project_item_home(p):
    href = primary_link(p)
    title = (f'<a class="title" href="{html.escape(href)}">{html.escape(p["name"])}</a>'
             if href else f'<span class="title">{html.escape(p["name"])}</span>')
    return (f'    <li>\n'
            f'      {title}\n'
            f'      <p class="desc">{html.escape(p["desc"])}</p>\n'
            f'    </li>')


def tool_item(t):
    return (f'    <li>\n'
            f'      <a class="title" href="{html.escape(t["link"])}">{html.escape(t["name"])}</a>\n'
            f'      <p class="desc">{html.escape(t["desc"])}</p>\n'
            f'    </li>')


def render_directory_page(active, heading, intro, items_html):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{heading} — {SITE_TITLE}</title>
  <meta name="description" content="{heading} by {SITE_TITLE}.">
  <link rel="stylesheet" href="style.css">
  <link rel="alternate" type="application/rss+xml" title="{SITE_TITLE} — Writing" href="feed.xml">
  {THEME_SNIPPET}
</head>
<body>
<div class="wrap">

{nav(active)}

  <h2 class="section">{heading}</h2>
  <p class="page-intro">{intro}</p>
  <ul class="list">
{items_html}
  </ul>

  <footer class="site">
    © 2026 {SITE_TITLE} · <a href="mailto:{SITE_EMAIL}">{SITE_EMAIL}</a>
  </footer>

</div>
<script src="site.js"></script>
</body>
</html>
"""


def render_feed(posts):
    items = []
    for p in posts:
        items.append(f"""    <item>
      <title>{html.escape(p['title'])}</title>
      <link>{SITE_URL}/posts/{p['slug']}.html</link>
      <guid>{SITE_URL}/posts/{p['slug']}.html</guid>
      <pubDate>{p['_date_rss']}</pubDate>
      <description>{html.escape(p['description'])}</description>
    </item>""")
    body = "\n\n".join(items)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{SITE_TITLE} — Writing</title>
    <link>{SITE_URL}/</link>
    <description>Blog posts and notes by {SITE_TITLE}.</description>
    <language>en</language>
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>

{body}

  </channel>
</rss>
"""


def patch_index(posts, projects, tools):
    path = os.path.join(ROOT, "index.html")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    featured = [p for p in projects if p.get("featured")]
    sections = {
        "POSTS": list_items(posts[:RECENT_ON_HOME]),
        "PROJECTS": "\n".join(project_item_home(p) for p in featured),
        "TOOLS": "\n".join(tool_item(t) for t in tools),
    }
    for marker, snippet in sections.items():
        text = re.sub(
            rf"(<!-- {marker}:START -->).*?(<!-- {marker}:END -->)",
            lambda m, s=snippet: m.group(1) + "\n" + s + "\n    " + m.group(2),
            text, flags=re.S,
        )
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


# ---------------------------------------------------------------- main
def main():
    os.makedirs(POSTS, exist_ok=True)
    posts = []
    for fname in os.listdir(CONTENT):
        if not fname.endswith(".md"):
            continue
        slug = os.path.splitext(fname)[0]
        with open(os.path.join(CONTENT, fname), encoding="utf-8") as f:
            meta, body_md = parse_front_matter(f.read())
        if str(meta.get("draft", "")).lower() == "true":
            continue
        d = datetime.datetime.strptime(meta["date"].strip(), "%Y-%m-%d")
        meta["_date_obj"] = d
        meta["_date_display"] = d.strftime("%b ") + str(d.day) + d.strftime(", %Y")
        meta["_date_rss"] = d.strftime("%a, %d %b %Y 09:00:00 +0000")
        meta["slug"] = slug
        meta["title"] = unquote(meta.get("title", slug))
        meta["description"] = unquote(meta.get("description", ""))
        html_body = convert_markdown(body_md)
        with open(os.path.join(POSTS, slug + ".html"), "w", encoding="utf-8") as f:
            f.write(render_post(meta, html_body))
        posts.append(meta)

    posts.sort(key=lambda p: p["_date_obj"], reverse=True)

    projects = load_data("projects")
    tools = load_data("tools")

    with open(os.path.join(ROOT, "writing.html"), "w", encoding="utf-8") as f:
        f.write(render_writing(posts))
    with open(os.path.join(ROOT, "projects.html"), "w", encoding="utf-8") as f:
        f.write(render_directory_page(
            "projects", "Projects",
            "Things I've built. Source where it's public, writeups where it isn't.",
            "\n".join(project_item(p) for p in projects)))
    with open(os.path.join(ROOT, "tools.html"), "w", encoding="utf-8") as f:
        f.write(render_directory_page(
            "tools", "Tools",
            "Things you can use right now.",
            "\n".join(tool_item(t) for t in tools)))
    with open(os.path.join(ROOT, "feed.xml"), "w", encoding="utf-8") as f:
        f.write(render_feed(posts))
    patch_index(posts, projects, tools)

    print(f"Built {len(posts)} post(s), {len(projects)} project(s), {len(tools)} tool(s):")
    for p in posts:
        print(f"  {p['_date_display']:>14}  {p['slug']}")


if __name__ == "__main__":
    main()

# nestwork — site branch

This orphan branch holds the GitHub Pages landing site only. It shares no
history with `main`, so the template repo stays pure markdown and nobody who
clicks **Use this template** inherits a frontend project.

## Layout

- `src/page.html` — the single bilingual source. Content is written once with
  paired `lang="en"` / `lang="zh"` elements. Do not nest a same-name tag inside
  a `lang` element (the build splits on it); wrap inline text in bare `<span>`.
- `build.py` — emits `index.html` (English) and `zh/index.html` (Chinese) as
  fully static pages with their own canonical URL and hreflang pairs, plus
  `sitemap.xml`. FAQ markup and its FAQPage JSON-LD come from one list in the
  script, so they cannot drift. It fails on leftover other-language elements,
  unfilled placeholders, duplicate ids, unbalanced tags or more than one `<h1>`.
- `src/og.html` — source of the 1200×630 share images `og.png` / `og-zh.png`.
- No external requests at runtime: no web fonts, no analytics, no CDN.

## Editing

```bash
python3 build.py            # regenerate index.html, zh/index.html, sitemap.xml
```

Commit the generated files with the source; Pages serves them as-is.

When `VERSION` or the protocol version changes on `main`, update `PROTOCOL` /
`VERSION` / `UPDATED` at the top of `build.py` and rebuild.

To refresh the share images, screenshot `src/og.html` and
`src/og.html?lang=zh` at 1200×630 with any headless browser.

## Search

`robots.txt` must live at the domain root (`songth1ef.github.io`), which this
project site does not control; crawling is allowed by default. Submit
`https://songth1ef.github.io/nestwork/sitemap.xml` in Google Search Console and
Bing Webmaster Tools under a URL-prefix property.

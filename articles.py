"""Article pages for the nestwork site: markdown in content/articles -> static HTML.

Zero dependencies. Supports the markdown subset in content/WRITING-SPEC.md plus
images. Each topic is a pair `<slug>.en.md` / `<slug>.zh.md`; both languages get
their own URL with hreflang, Article + BreadcrumbList (+ FAQPage) JSON-LD, and
an entry in the article index and sitemap.
"""
import html
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content" / "articles"
REPO_BLOB = "https://github.com/songth1ef/nestwork/blob/main/"
BLOG_LINK = re.compile(r"https://github\.com/songth1ef/nestwork/blob/main/docs/blog/([a-z0-9-]+?)(?:\.zh)?\.md")

UI = {
    "en": {
        "html_lang": "en", "og_locale": "en_US", "home": "Home", "articles": "Articles",
        "index_title": "AI Agent Memory Articles & Guides — nestwork",
        "index_h1": "Articles on AI agent memory",
        "index_desc": "Guides on AI agent memory: Claude Code and Codex memory across machines, multi-agent shared memory, benchmarks, encryption and git-native context.",
        "index_lede": "Practical guides on giving AI coding agents long-term memory — across sessions, machines and tools. Every claim is checked against the nestwork source or linked to its origin.",
        "stories": "Stories", "guides": "Guides", "min": "min read", "updated": "Updated",
        "toc": "On this page", "cta_h": "Give your agents a memory",
        "cta_p": "nestwork turns one private git repo into shared, persistent memory for Claude Code, Codex, Gemini, Kimi and more.",
        "cta_btn": "Use this template →", "cta_star": "★ Star on GitHub", "switch": "中文", "all": "All articles",
    },
    "zh": {
        "html_lang": "zh-CN", "og_locale": "zh_CN", "home": "首页", "articles": "文章",
        "index_title": "AI Agent 记忆文章与指南 — nestwork",
        "index_h1": "AI agent 记忆：文章与指南",
        "index_desc": "AI agent 记忆实战指南：Claude Code 与 Codex 跨机器记忆、多 agent 共享记忆、基准测试、加密与 git 原生上下文。",
        "index_lede": "给 AI 编程 agent 加长期记忆的实用指南——跨会话、跨机器、跨工具。每条说法都对照过 nestwork 源码，或附上了原始出处。",
        "stories": "故事", "guides": "指南", "min": "分钟阅读", "updated": "更新于",
        "toc": "本文目录", "cta_h": "给你的 agent 一份记忆",
        "cta_p": "nestwork 把一个私有 git 仓库变成 Claude Code、Codex、Gemini、Kimi 等 agent 共享的长期记忆。",
        "cta_btn": "用模板创建我的记忆仓库 →", "cta_star": "★ 去 GitHub 点个 Star", "switch": "EN", "all": "全部文章",
    },
}


# ---------------------------------------------------------------- parsing

def parse(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path.name}: missing front matter")
    end = text.index("\n---", 4)
    meta = {}
    for line in text[4:end].splitlines():
        key, _, value = line.partition(":")
        if key.strip():
            meta[key.strip()] = value.strip()
    body = text[end + 4:].lstrip("\n")
    for field in ("title", "description", "date"):
        if not meta.get(field):
            raise ValueError(f"{path.name}: front matter needs `{field}`")
    return meta, body


def jpeg_size(path):
    data = path.read_bytes()
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    raise ValueError(f"no size in {path}")


# ---------------------------------------------------------------- markdown

def slugify(text):
    s = re.sub(r"<[^>]+>", "", text).lower()
    s = re.sub(r"[^\w一-鿿]+", "-", s).strip("-")
    return s or "section"


def inline(text, ctx):
    codes = []

    def stash(m):
        codes.append(f"<code>{html.escape(m.group(1))}</code>")
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text, quote=False)

    def link(m):
        label, url = m.group(1), html.unescape(m.group(2))
        url = BLOG_LINK.sub(lambda b: f"../{b.group(1)}/", url)
        ctx["links"].append(url)
        ext = url.startswith("http")
        attrs = ' rel="noopener"' if ext else ""
        return f'<a href="{html.escape(url, quote=True)}"{attrs}>{label}</a>'

    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], text)


def render_markdown(body, ctx):
    lines = body.split("\n")
    out, i = [], 0
    ctx.setdefault("headings", [])
    ctx.setdefault("links", [])
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            lang = line[3:].strip()
            i += 1
            code = []
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            out.append(f'<pre class="code"><code data-lang="{html.escape(lang)}">{html.escape(chr(10).join(code))}</code></pre>')
            continue
        m = re.match(r"^(#{2,4}) (.+)$", line)
        if m:
            level = len(m.group(1))
            content = inline(m.group(2).strip(), ctx)
            hid = slugify(m.group(2))
            if level == 2:
                ctx["headings"].append((hid, re.sub(r"<[^>]+>", "", content)))
            out.append(f'<h{level} id="{hid}">{content}</h{level}>')
            i += 1
            continue
        m = re.match(r"^!\[([^\]]*)\]\(([^)\s]+)\)\s*$", line)
        if m:
            alt, src = m.group(1), m.group(2)
            name = src.split("/")[-1]
            img = ROOT / "articles" / "img" / name
            if not img.is_file():
                raise ValueError(f"missing image {name}")
            w, h = jpeg_size(img)
            ctx["images"] = ctx.get("images", 0) + 1
            loading = "eager" if ctx["images"] == 1 else "lazy"
            out.append(f'<figure><img src="{ctx["root"]}articles/img/{name}" alt="{html.escape(alt, quote=True)}" '
                       f'width="{w}" height="{h}" loading="{loading}" decoding="async"></figure>')
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = re.split(r"(?<!\\)\|", lines[i].strip().strip("|"))
                rows.append([c.strip().replace("\\|", "|") for c in cells])
                i += 1
            head, body_rows = rows[0], [r for r in rows[2:]]
            th = "".join(f"<th>{inline(c, ctx)}</th>" for c in head)
            trs = "".join("<tr>" + "".join(f"<td>{inline(c, ctx)}</td>" for c in r) + "</tr>" for r in body_rows)
            out.append(f'<div class="table-wrap"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>')
            continue
        if line.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].startswith(">"):
                quote.append(lines[i].lstrip(">").strip())
                i += 1
            out.append(f"<blockquote><p>{inline(' '.join(quote), ctx)}</p></blockquote>")
            continue
        m = re.match(r"^(- |\d+\. )", line)
        if m:
            ordered = not line.startswith("- ")
            items = []
            while i < len(lines) and re.match(r"^(- |\d+\. )", lines[i]):
                item = re.sub(r"^(- |\d+\. )", "", lines[i])
                i += 1
                while i < len(lines) and lines[i].startswith("  ") and lines[i].strip():
                    item += " " + lines[i].strip()
                    i += 1
                items.append(f"<li>{inline(item, ctx)}</li>")
            tag = "ol" if ordered else "ul"
            start = int(m.group(1)[:-2]) if ordered else 1
            attr = f' start="{start}"' if start != 1 else ""
            out.append(f"<{tag}{attr}>{''.join(items)}</{tag}>")
            continue
        para = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{2,4} |```|\||>|- |\d+\. |!\[)", lines[i]):
            para.append(lines[i].strip())
            i += 1
        joiner = "" if ctx["lang"] == "zh" else " "
        out.append(f"<p>{inline(joiner.join(para), ctx)}</p>")
    return "\n".join(out)


def extract_faq(body):
    m = re.search(r"^## (FAQ|常见问题)\s*$(.*?)(?=^## |\Z)", body, re.M | re.S)
    if not m:
        return []
    faq = []
    for q in re.finditer(r"^### (.+?)\s*$(.*?)(?=^### |\Z)", m.group(2), re.M | re.S):
        answer = re.sub(r"\s+", " ", re.sub(r"[`*]|\[([^\]]+)\]\([^)]+\)", r"\1", q.group(2))).strip()
        if answer:
            faq.append((q.group(1).strip(), answer))
    return faq


# ---------------------------------------------------------------- collection

def load(base):
    """Return {slug: {lang: article}} for every pair in content/articles."""
    found = {}
    for path in sorted(CONTENT.glob("*.md")):
        m = re.match(r"^([a-z0-9-]+)\.(en|zh)\.md$", path.name)
        if not m:
            continue
        slug, lang = m.groups()
        meta, body = parse(path)
        found.setdefault(slug, {})[lang] = {"slug": slug, "lang": lang, "meta": meta, "body": body, "path": path}
    for slug, pair in found.items():
        for lang, art in pair.items():
            art["url"] = f"{base}{'zh/' if lang == 'zh' else ''}articles/{slug}/"
            art["out"] = ROOT / ("zh/" if lang == "zh" else "") / "articles" / slug / "index.html"
            art["root"] = "../../../" if lang == "zh" else "../../"
    return found


def reading_minutes(body, lang):
    text = re.sub(r"```.*?```", "", body, flags=re.S)
    units = len(re.findall(r"[一-鿿]", text)) / 400 if lang == "zh" else len(text.split()) / 230
    return max(2, round(units))

#!/usr/bin/env python3
"""Build the static landing pages from src/page.html.

src/page.html is written once with paired `lang="en"` / `lang="zh"` elements.
This script emits one fully static page per language (index.html and
zh/index.html) so each language has its own crawlable URL with hreflang,
instead of hiding one language with CSS. FAQ markup and its JSON-LD come from
the same FAQ list below, so the visible answers and the structured data cannot
drift apart. Run: python3 build.py   (no dependencies)
"""
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path

import articles as A
import privacy_guard

ROOT = Path(__file__).resolve().parent
BASE = "https://songth1ef.github.io/nestwork/"
REPO = "https://github.com/songth1ef/nestwork"
PROTOCOL = "3.1"
VERSION = "0.6.0"
UPDATED = "2026-09-27"  # bump when page content changes

PAGES = {
    "en": {
        "out": ROOT / "index.html",
        "html_lang": "en",
        "canonical": BASE,
        "og_locale": "en_US",
        "og_image": BASE + "og.png",
        "og_alt": "nestwork: your agents remember. One private git repo as shared memory for every AI coding agent.",
        "title": "nestwork — AI Agent Memory for Claude Code, Codex & Gemini",
        "description": "Git-native AI agent memory: give Claude Code, Codex, Gemini and Kimi one persistent memory across sessions, machines and tools. No server, no lock-in.",
        "switch_href": "zh/", "switch_lang": "zh", "switch_hreflang": "zh-CN", "switch_label": "中文",
        "nav_label": "Primary",
        "term_label": "Example session start: the agent loads two resident files and lists the rest as on-demand.",
        "tree_label": "Repository layout of a nestwork memory repo",
        "bars_label": "Tokens loaded per session: 69.6k for a 2.x full startup, 3.6k for a 3.x git task, 640 for a 3.x startup.",
        "chain_label": "Authority chain from highest to lowest",
        "tools_label": "Supported tools",
        "asset": "",
        "art_label": "Illustration: a laptop, a desktop, a cloud server and a phone, each running an agent, all syncing to one private git repository.",
        "copy": "COPY", "copied": "COPIED",
    },
    "zh": {
        "out": ROOT / "zh" / "index.html",
        "html_lang": "zh-CN",
        "canonical": BASE + "zh/",
        "og_locale": "zh_CN",
        "og_image": BASE + "og-zh.png",
        "og_alt": "nestwork：让你的 AI agent 记得住。一个私有 git 仓库，作为所有 AI 编程 agent 的共享记忆。",
        "title": "nestwork：AI Agent 记忆，让 Claude Code、Codex 共享长期记忆",
        "description": "git 原生的 AI agent 记忆：让 Claude Code、Codex、Gemini、Kimi 跨会话、跨机器、跨工具共享同一份长期记忆，无需服务器，不被厂商锁定。",
        "switch_href": "../", "switch_lang": "en", "switch_hreflang": "en", "switch_label": "EN",
        "nav_label": "主导航",
        "term_label": "会话启动示例：agent 只加载两个常驻文件，其余列为按需读取。",
        "tree_label": "nestwork 记忆仓库的目录结构",
        "bars_label": "每次会话读入的 token：2.x 全量启动 69.6k，3.x 做一次 git 操作 3.6k，3.x 启动 640。",
        "chain_label": "从高到低的权威链",
        "tools_label": "支持的工具",
        "asset": "../",
        "art_label": "示意图：笔记本、台式机、云服务器和手机上各有一个 agent，都同步到同一个私有 git 仓库。",
        "copy": "复制", "copied": "已复制",
    },
}

FAQ = [
    {
        "en": ("What is nestwork?",
               "<p>nestwork is a git-native memory protocol for AI coding agents. A private git repository holds your rules, preferences, lessons and project context as plain markdown, and every agent you use — Claude Code, Codex CLI, Gemini CLI, Kimi Code, Hermes, OpenClaw — reads and writes that same repository. The result is one persistent, versioned memory that follows you across sessions, machines and vendors.</p>"),
        "zh": ("nestwork 是什么？",
               "<p>nestwork 是一套面向 AI 编程 agent 的 git 原生记忆协议。一个私有 git 仓库用普通 markdown 保存你的规矩、偏好、踩坑经验和项目上下文，你用的每个 agent——Claude Code、Codex CLI、Gemini CLI、Kimi Code、Hermes、OpenClaw——都读写同一个仓库。结果就是一份跨会话、跨机器、跨厂商的长期记忆，而且带版本历史。</p>"),
    },
    {
        "en": ("How do I share memory between Claude Code and Codex?",
               "<p>Clone your nest once per machine and run both installers: <code>scripts/install/claude.sh</code> and <code>scripts/install/codex.sh</code>. Both tools get the same startup protocol pointing at the same repository, so a rule or lesson written in a Claude Code session is available to Codex in its next session, and vice versa. Each tool writes to its own directory, so they never overwrite each other.</p>"),
        "zh": ("怎么让 Claude Code 和 Codex 共享记忆？",
               "<p>在每台机器上 clone 一次你的记忆仓库，然后分别运行 <code>scripts/install/claude.sh</code> 和 <code>scripts/install/codex.sh</code>。两个工具会拿到指向同一仓库的同一套启动协议：在 Claude Code 里记下的规则或教训，Codex 下个会话就能用，反之亦然。每个工具只写自己的目录，互不覆盖。</p>"),
    },
    {
        "en": ("Does Claude Code's memory sync across machines?",
               "<p>Not by itself. As of 2026, Claude Code, Codex and Kimi Code all keep their built-in memory on the local machine. nestwork puts the durable part of that context in git, so a new laptop or cloud box gets it with a single <code>git clone</code>. You can also distill a tool's native memory into the nest so it survives a machine change, a tool change or a lost account.</p>"),
        "zh": ("Claude Code 的记忆能跨机器同步吗？",
               "<p>它自己不能。截至 2026 年，Claude Code、Codex、Kimi Code 的内置记忆都只存在本机。nestwork 把其中值得长期保留的上下文放进 git，新电脑或云服务器 <code>git clone</code> 一下就有了。你也可以把工具的原生记忆蒸馏进仓库，这样换机器、换工具、丢账号都不会丢。</p>"),
    },
    {
        "en": ("Won't loading all that memory bloat my context window?",
               "<p>No — that is exactly what the protocol avoids. At startup an agent reads only a small resident tier: core rules plus two short summaries, about 640 tokens on the author's nest versus roughly 69,600 for a load-everything startup. Everything else is on demand: <code>memory.md</code> is a generated index of topic files, each with a one-line description of when to read it, and the agent opens only the files that match the current task.</p>"),
        "zh": ("记忆越攒越多，会不会把上下文窗口撑爆？",
               "<p>不会，协议正是为此设计的。启动时 agent 只读很小的常驻层：核心规则加两份简短摘要，在作者的仓库上约 640 token，而全量加载要约 69,600 token。其余都按需读取：<code>memory.md</code> 是自动生成的主题索引，每个主题文件都有一行「什么时候该读」的描述，agent 只打开与当前任务匹配的文件。</p>"),
    },
    {
        "en": ("Is nestwork a vector database or a RAG system?",
               "<p>No. There are no embeddings and no retrieval service. Memory is human-readable markdown that you can open, edit, diff and review like any other file in git. Retrieval works the way an agent already uses skills: read a short index, pick the relevant file, read it.</p>"),
        "zh": ("nestwork 是向量数据库或 RAG 吗？",
               "<p>不是。没有 embedding，也没有检索服务。记忆就是人能直接读的 markdown，可以像 git 里其他文件一样打开、编辑、diff 和审阅。检索方式和 agent 使用 skill 一样：读一份简短的索引，挑出相关文件，再读它。</p>"),
    },
    {
        "en": ("Do I need to run a server or pay for a service?",
               "<p>No. There is no hosted service, daemon or database — only git and a few shell and Python scripts in your own repository. Host it on GitHub, GitLab, a self-hosted Gitea or any git remote you already use. Agents can read memory without a network; on tools with sync hooks, memory writes need the remote to be reachable.</p>"),
        "zh": ("需要部署服务器或付费吗？",
               "<p>不需要。没有托管服务、没有常驻进程、没有数据库，只有 git 和你仓库里的几份 shell / Python 脚本。托管在 GitHub、GitLab、自建 Gitea 或任何你已有的 git 远端都行。断网时 agent 仍能读取记忆；在装了同步 hook 的工具上，写入记忆需要能连上远端。</p>"),
    },
    {
        "en": ("What happens when many agents write at the same time?",
               "<p>Every agent instance owns its own directory, <code>agents/&lt;host&gt;/&lt;agent-id&gt;/</code>, so ordinary memory writes never touch the same file. On tools with hooks, each write runs <code>pull --rebase</code> first and commit + push right after, with retries. Shared memory is only rewritten during an explicit, human-reviewed distillation.</p>"),
        "zh": ("很多 agent 同时写，会冲突吗？",
               "<p>每个 agent 实例独占自己的目录 <code>agents/&lt;host&gt;/&lt;agent-id&gt;/</code>，日常写记忆根本不会碰到同一个文件。在支持 hook 的工具上，每次写入前自动 <code>pull --rebase</code>，写完立即 commit + push，失败会重试。共享记忆只在明确触发、经人审核的蒸馏中才会被改写。</p>"),
    },
    {
        "en": ("Can I keep sensitive memory private?",
               "<p>Keep the repository private — that is enough for most people. For content that must stay confidential even from your git host, enable the optional git-crypt mode: agents read and write plain text while every commit stores ciphertext. Never store API keys or secrets in memory, encrypted or not; use a secret manager.</p>"),
        "zh": ("敏感的记忆能保密吗？",
               "<p>把仓库设为私有，对大多数人已经足够。如果连 git 托管方也不能看到，可以开启可选的 git-crypt 模式：agent 读写明文，提交进 git 的全是密文。无论是否加密，都不要把 API key 或密码写进记忆，它们应该放在专门的密钥管理工具里。</p>"),
    },
    {
        "en": ("How is this different from AGENTS.md or CLAUDE.md?",
               "<p>A per-repository <code>AGENTS.md</code> describes one codebase. nestwork uses the same file format as a startup protocol for a user-level memory repository, so your identity, preferences, cross-project lessons and live project state travel with you into every repository and every tool — while each project's own <code>AGENTS.md</code> keeps working as before.</p>"),
        "zh": ("它和 AGENTS.md / CLAUDE.md 有什么区别？",
               "<p>单个仓库里的 <code>AGENTS.md</code> 只描述那一个代码库。nestwork 用同样的文件格式，作为一个「用户级记忆仓库」的启动协议：你的身份、偏好、跨项目的经验和在飞项目状态，会跟着你进入每一个仓库、每一个工具；各项目自己的 <code>AGENTS.md</code> 照常生效。</p>"),
    },
    {
        "en": ("Can a team use nestwork?",
               "<p>Yes, but start small: one private repository, one directory per agent instance, and human-owned rules in <code>queen/</code>, which agents treat as read-only. The layered authority chain decides whose instruction wins, so shared rules stay stable while each agent keeps its own notes.</p>"),
        "zh": ("团队可以用吗？",
               "<p>可以，但建议从小处开始：一个私有仓库，每个 agent 实例一个目录，规则放在由人维护、agent 只读的 <code>queen/</code> 里。分层的权威链决定谁的指令优先，共享规则保持稳定，每个 agent 又各自保留自己的笔记。</p>"),
    },
]

READS = [
    ("en", "I gave 16 AI agents one shared brain, using nothing but git", "docs/blog/16-agents-one-brain.md", "story"),
    ("zh", "我用 git 给 16 个 AI agent 装了同一个大脑", "docs/blog/16-agents-one-brain.zh.md", "故事"),
    ("en", "Your AI agent forgets everything when you switch devices", "docs/blog/agent-amnesia-cross-device.md", "essay"),
    ("zh", "换台设备，你的 AI agent 就失忆了", "docs/blog/agent-amnesia-cross-device.zh.md", "随笔"),
    ("en", "AI agent memory is a protocol problem, not a database problem", "docs/blog/memory-is-a-protocol-problem.md", "essay"),
    ("zh", "AI agent 记忆不是数据库问题，而是协议问题", "docs/blog/memory-is-a-protocol-problem.zh.md", "随笔"),
    ("en", "Claude Code memory across machines", "docs/claude-code-memory.md", "guide"),
    ("zh", "Claude Code 跨机器记忆（英文）", "docs/claude-code-memory.md", "指南"),
    ("en", "Persistent memory for Codex CLI", "docs/codex-persistent-memory.md", "guide"),
    ("zh", "Codex CLI 长期记忆（英文）", "docs/codex-persistent-memory.md", "指南"),
    ("en", "Shared context for AI coding agents", "docs/shared-context-for-ai-coding-agents.md", "guide"),
    ("zh", "AI 编程 agent 的共享上下文（英文）", "docs/shared-context-for-ai-coding-agents.md", "指南"),
    ("en", "The AI agent memory landscape", "docs/comparisons/agent-memory-landscape.md", "compare"),
    ("zh", "AI agent 记忆方案全景（英文）", "docs/comparisons/agent-memory-landscape.md", "对比"),
    ("en", "nestwork vs claude-mem", "docs/comparisons/claude-mem.md", "compare"),
    ("zh", "nestwork 与 claude-mem 对比（英文）", "docs/comparisons/claude-mem.md", "对比"),
    ("en", "Resident and on-demand context loading", "docs/context-loading.md", "protocol"),
    ("zh", "常驻与按需的上下文加载（英文）", "docs/context-loading.md", "协议"),
    ("en", "The full protocol: AGENTS.md", "AGENTS.md", "protocol"),
    ("zh", "协议全文：AGENTS.md（英文）", "AGENTS.md", "协议"),
]

LANG_ELEMENT = re.compile(r'<(\w+)((?:(?!\blang=)[^>])*)\slang="(en|zh)"([^>]*)>(.*?)</\1>', re.S)
PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")
PIXEL = re.compile(r"\{\{px:(\w+):([0-9a-f]{3,6}):([0-9a-f]{3,6})\}\}")

# 10x10 pixel sprites: "#" = foreground, "." = background.
SPRITES = {
    "bot": [
        "....##....",
        "....##....",
        ".########.",
        ".#......#.",
        ".#.##.#.#.",
        ".#......#.",
        ".#.####.#.",
        ".########.",
        "..#....#..",
        ".##....##.",
    ],
    "bot2": [
        "..######..",
        ".#......#.",
        "#..#..#..#",
        "#..#..#..#",
        "#........#",
        "#.######.#",
        ".#......#.",
        "..######..",
        "...#..#...",
        "..##..##..",
    ],
}


def pixel_svg(match):
    name, fg, bg = match.groups()
    rows = SPRITES[name]
    rects = "".join(
        f'<rect x="{x}" y="{y}" width="1" height="1"/>'
        for y, row in enumerate(rows) for x, ch in enumerate(row) if ch == "#"
    )
    w, h = len(rows[0]), len(rows)
    return (f'<svg class="px" viewBox="-1 -1 {w + 2} {h + 2}" aria-hidden="true">'
            f'<rect x="-1" y="-1" width="{w + 2}" height="{h + 2}" fill="#{bg}"/><g fill="#{fg}">{rects}</g></svg>')


def strip_tags(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def faq_html(lang):
    items = []
    for i, entry in enumerate(FAQ):
        q, a = entry[lang]
        opened = " open" if i == 0 else ""
        items.append(f'<details{opened}><summary>{html.escape(q)}</summary><div class="answer">{a}</div></details>')
    return "\n      ".join(items)


GUIDE_ORDER = [
    "ai-agent-memory", "claude-code-memory-across-machines", "share-memory-claude-code-codex",
    "codex-cli-persistent-memory", "agent-memory-tools-compared", "agent-memory-benchmarks",
    "agents-md-vs-claude-md-vs-memory", "topic-memory-on-demand-loading", "multi-agent-memory-without-conflicts",
    "git-native-agent-memory", "memory-distillation", "agent-mailbox-git", "encrypt-agent-memory-git-crypt",
    "rescue-tool-native-memory", "long-term-memory-in-practice", "nestwork-getting-started-faq",
]
STORY_ORDER = ["16-agents-one-brain", "agent-amnesia-cross-device", "memory-is-a-protocol-problem", "nestwork-overview"]


def ordered(arts):
    known = [s for s in GUIDE_ORDER + STORY_ORDER if s in arts]
    return known + sorted(s for s in arts if s not in known)


def reads_html(lang, arts):
    rows = []
    for slug in ordered(arts)[:12]:
        art = arts[slug][lang]
        kind = A.UI[lang]["stories"] if art["meta"].get("type") == "story" else A.UI[lang]["guides"]
        rows.append(f'<li><a href="articles/{slug}/">{html.escape(art["meta"]["title"])}'
                    f'<span class="t">{html.escape(kind)}</span></a></li>')
    rows.append(f'<li><a href="articles/"><b>{html.escape(A.UI[lang]["all"])} →</b><span class="t">{len(arts)}</span></a></li>')
    return "\n        ".join(rows)


def jsonld(lang, page):
    graph = [
        {
            "@type": "WebSite",
            "@id": BASE + "#website",
            "url": BASE,
            "name": "nestwork",
            "inLanguage": ["en", "zh-CN"],
        },
        {
            "@type": "WebPage",
            "@id": page["canonical"] + "#webpage",
            "url": page["canonical"],
            "name": page["title"],
            "description": page["description"],
            "inLanguage": page["html_lang"],
            "isPartOf": {"@id": BASE + "#website"},
            "about": {"@id": BASE + "#software"},
            "dateModified": UPDATED,
        },
        {
            "@type": "SoftwareApplication",
            "@id": BASE + "#software",
            "name": "nestwork",
            "applicationCategory": "DeveloperApplication",
            "operatingSystem": "macOS, Linux, Windows",
            "softwareVersion": VERSION,
            "description": PAGES["en"]["description"],
            "url": BASE,
            "downloadUrl": REPO,
            "codeRepository": REPO,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            "author": {"@type": "Person", "name": "songth1ef", "url": "https://github.com/songth1ef"},
            "keywords": "AI agent memory, persistent memory, Claude Code, Codex CLI, Gemini CLI, Kimi Code, AGENTS.md, git, shared context",
        },
        {
            "@type": "FAQPage",
            "@id": page["canonical"] + "#faq",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": entry[lang][0],
                    "acceptedAnswer": {"@type": "Answer", "text": strip_tags(entry[lang][1])},
                }
                for entry in FAQ
            ],
        },
    ]
    text = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))
    return text.replace("</", "<\\/")


def select_language(source, lang):
    def pick(match):
        tag, before, which, after, inner = match.groups()
        if which != lang:
            return ""
        attrs = (before + after).rstrip()
        if tag == "span" and not attrs.strip():
            return inner
        return f"<{tag}{attrs}>{inner}</{tag}>"

    previous = None
    while previous != source:
        previous, source = source, LANG_ELEMENT.sub(pick, source)
    return source


class Balance(HTMLParser):
    VOID = {"meta", "link", "br", "img", "input", "hr", "source", "rect", "path", "circle"}

    def __init__(self):
        super().__init__()
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"unexpected </{tag}> (open: {self.stack[-3:]})")
            if tag in self.stack:
                while self.stack and self.stack.pop() != tag:
                    pass
        else:
            self.stack.pop()


def check(page_html, lang):
    other = "zh" if lang == "en" else "en"
    problems = []
    if re.search(rf'\slang="{other}"', page_html):
        problems.append(f'leftover lang="{other}" element')
    if PLACEHOLDER.search(page_html):
        problems.append(f"unfilled placeholder {PLACEHOLDER.search(page_html).group(0)}")
    if len(re.findall(r"<h1\b", page_html)) != 1:
        problems.append("page must have exactly one <h1>")
    ids = re.findall(r'\sid="([^"]+)"', page_html)
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        problems.append(f"duplicate ids: {sorted(dupes)}")
    parser = Balance()
    parser.feed(page_html)
    problems += parser.errors
    if parser.stack:
        problems.append(f"unclosed tags: {parser.stack}")
    if lang == "zh" and re.search(r"[一-鿿]", page_html) is None:
        problems.append("zh page has no Chinese text")
    return problems


def alternates(en_url, zh_url):
    return (("en", en_url), ("zh-CN", zh_url), ("x-default", en_url))


def sitemap(arts):
    entries = [(BASE, BASE + "zh/", UPDATED), (BASE + "articles/", BASE + "zh/articles/", UPDATED)]
    for slug in ordered(arts):
        pair = arts[slug]
        lastmod = max(pair["en"]["meta"].get("updated", pair["en"]["meta"]["date"]),
                      pair["zh"]["meta"].get("updated", pair["zh"]["meta"]["date"]))
        entries.append((pair["en"]["url"], pair["zh"]["url"], lastmod))
    urls = []
    for en_url, zh_url, lastmod in entries:
        alts = "".join(f'\n    <xhtml:link rel="alternate" hreflang="{h}" href="{u}"/>' for h, u in alternates(en_url, zh_url))
        for loc in (en_url, zh_url):
            urls.append(f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lastmod}</lastmod>{alts}\n  </url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(urls) + "\n</urlset>\n")


def hreflang_links(en_url, zh_url):
    return "\n".join(f'<link rel="alternate" hreflang="{h}" href="{u}">' for h, u in alternates(en_url, zh_url))


def card(art, href):
    return (f'<a href="{href}"><b>{html.escape(art["meta"]["title"])}</b>'
            f'<span>{html.escape(art["meta"]["description"])}</span></a>')


def fill(template, values):
    return PLACEHOLDER.sub(lambda m: values[m.group(1)] if m.group(1) in values else m.group(0), template)


def article_jsonld(art, lang, faq, kind_type):
    ui = A.UI[lang]
    meta = art["meta"]
    home = BASE + ("zh/" if lang == "zh" else "")
    graph = [
        {
            "@type": kind_type, "@id": art["url"] + "#article", "headline": meta["title"][:110],
            "description": meta["description"], "inLanguage": ui["html_lang"],
            "datePublished": meta["date"], "dateModified": meta.get("updated", meta["date"]),
            "author": {"@type": "Person", "name": "songth1ef", "url": "https://github.com/songth1ef"},
            "publisher": {"@type": "Organization", "name": "nestwork", "url": BASE},
            "image": [BASE + ("og-zh.png" if lang == "zh" else "og.png")],
            "mainEntityOfPage": art["url"], "isPartOf": {"@id": BASE + "#website"},
            "about": {"@id": BASE + "#software"},
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": ui["home"], "item": home},
                {"@type": "ListItem", "position": 2, "name": ui["articles"], "item": home + "articles/"},
                {"@type": "ListItem", "position": 3, "name": meta["title"], "item": art["url"]},
            ],
        },
    ]
    if faq:
        graph.append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]})
    text = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))
    return text.replace("</", "<\\/")


def build_articles(arts):
    template = (ROOT / "src" / "article.html").read_text(encoding="utf-8")
    problems = []
    order = ordered(arts)
    for slug in order:
        for lang in ("en", "zh"):
            art = arts[slug][lang]
            other = arts[slug]["zh" if lang == "en" else "en"]
            ui = A.UI[lang]
            meta = art["meta"]
            ctx = {"lang": lang, "root": art["root"]}
            body = A.render_markdown(art["body"], ctx)
            faq = A.extract_faq(art["body"])
            for link in ctx["links"]:
                if link.startswith("../") and link != "../":
                    target = link[3:].strip("/").split("#")[0]
                    if target not in arts:
                        problems.append(f"{slug}.{lang}: link to unknown article {link}")
            limit_t, limit_d = (65, 160) if lang == "en" else (34, 90)
            seo_title = meta.get("seo_title") or meta["title"]
            if len(seo_title) > limit_t:
                problems.append(f"{slug}.{lang}: title {len(seo_title)} chars > {limit_t} (add seo_title)")
            if len(meta["description"]) > limit_d:
                problems.append(f"{slug}.{lang}: description {len(meta['description'])} chars > {limit_d}")
            is_story = meta.get("type") == "story"
            others = [s for s in order if s != slug]
            more = "".join(card(arts[s][lang], f"../{s}/") for s in others[:6])
            toc = "".join(f'<a href="#{hid}">{html.escape(text)}</a>' for hid, text in ctx["headings"])
            home_url = art["root"] + ("zh/" if lang == "zh" else "")
            values = {k: html.escape(v, quote=True) for k, v in ui.items()}
            values.update({
                "title": html.escape(meta["title"], quote=True),
                "seo_title": html.escape(seo_title if len(seo_title) > 45 else f"{seo_title} — nestwork", quote=True),
                "description": html.escape(meta["description"], quote=True),
                "url": art["url"], "root": art["root"], "og_type": "article",
                "og_image": BASE + ("og-zh.png" if lang == "zh" else "og.png"),
                "hreflang": hreflang_links(arts[slug]["en"]["url"], arts[slug]["zh"]["url"]),
                "home_url": home_url, "index_url": "../",
                "switch_url": art["root"] + ("zh/" if other["lang"] == "zh" else "") + f"articles/{slug}/", "switch_lang": other["lang"],
                "switch_hreflang": "zh-CN" if other["lang"] == "zh" else "en",
                "kind": html.escape(ui["stories"] if is_story else ui["guides"]),
                "minutes": str(A.reading_minutes(art["body"], lang)),
                "date": meta.get("updated", meta["date"]),
                "body": body, "toc_links": toc, "more_cards": more,
                "jsonld": article_jsonld(art, lang, faq, "BlogPosting" if is_story else "TechArticle"),
            })
            out = fill(template, values)
            if PLACEHOLDER.search(out):
                problems.append(f"{slug}.{lang}: unfilled {PLACEHOLDER.search(out).group(0)}")
            if re.search(r"\*\*|\]\(", re.sub(r"<pre.*?</pre>|<code>.*?</code>", "", out, flags=re.S)):
                problems.append(f"{slug}.{lang}: leftover markdown syntax")
            art["out"].parent.mkdir(parents=True, exist_ok=True)
            art["out"].write_text(out, encoding="utf-8")
    # index pages
    for lang in ("en", "zh"):
        ui = A.UI[lang]
        guides = [s for s in order if arts[s][lang]["meta"].get("type") != "story"]
        stories = [s for s in order if arts[s][lang]["meta"].get("type") == "story"]
        body = (f'<p>{html.escape(ui["index_lede"])}</p>'
                f'<h2 id="guides">{html.escape(ui["guides"])}</h2><div class="cards">'
                + "".join(card(arts[s][lang], f"{s}/") for s in guides) + "</div>"
                + f'<h2 id="stories">{html.escape(ui["stories"])}</h2><div class="cards">'
                + "".join(card(arts[s][lang], f"{s}/") for s in stories) + "</div>")
        index_url = BASE + ("zh/" if lang == "zh" else "") + "articles/"
        other_url = BASE + ("" if lang == "zh" else "zh/") + "articles/"
        root = "../../" if lang == "zh" else "../"
        values = {k: html.escape(v, quote=True) for k, v in ui.items()}
        itemlist = {"@context": "https://schema.org", "@type": "CollectionPage", "name": ui["index_h1"],
                    "url": index_url, "inLanguage": ui["html_lang"],
                    "mainEntity": {"@type": "ItemList", "itemListElement": [
                        {"@type": "ListItem", "position": i + 1, "url": arts[s][lang]["url"], "name": arts[s][lang]["meta"]["title"]}
                        for i, s in enumerate(guides + stories)]}}
        values.update({
            "title": html.escape(ui["index_h1"]), "seo_title": html.escape(ui["index_title"]),
            "description": html.escape(ui["index_desc"], quote=True), "url": index_url, "root": root,
            "og_type": "website", "og_image": BASE + ("og-zh.png" if lang == "zh" else "og.png"),
            "hreflang": hreflang_links(BASE + "articles/", BASE + "zh/articles/"),
            "home_url": "../", "index_url": "./", "switch_url": root + ("zh/" if lang == "en" else "") + "articles/",
            "switch_lang": "en" if lang == "zh" else "zh", "switch_hreflang": "en" if lang == "zh" else "zh-CN",
            "kind": html.escape(ui["articles"]), "minutes": str(len(guides) + len(stories)),
            "min": "篇" if lang == "zh" else "articles", "date": UPDATED, "body": body,
            "toc_links": f'<a href="#guides">{html.escape(ui["guides"])}</a><a href="#stories">{html.escape(ui["stories"])}</a>',
            "more_cards": "", "jsonld": json.dumps(itemlist, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"),
        })
        out = fill(template, values).replace('<section class="more"', '<section hidden class="more"').replace('<div class="wrap layout">', '<div class="wrap layout wide">')
        path = ROOT / ("zh/" if lang == "zh" else "") / "articles" / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(out, encoding="utf-8")
    return problems


def main():
    source = (ROOT / "src" / "page.html").read_text(encoding="utf-8")
    failed = False
    loaded = A.load(BASE)
    incomplete = sorted(s for s, pair in loaded.items() if set(pair) != {"en", "zh"})
    for slug in incomplete:
        print(f"SKIP {slug}: needs both .en.md and .zh.md")
    arts = {s: p for s, p in loaded.items() if s not in incomplete}
    for problem in build_articles(arts):
        print(f"FAIL {problem}")
        failed = True
    print(f"wrote {len(arts) * 2} article pages + 2 index pages")
    for lang, page in PAGES.items():
        values = {k: v for k, v in page.items() if isinstance(v, str)}
        values.update(
            lang=lang, url_en=BASE, url_zh=BASE + "zh/", protocol=PROTOCOL, version=VERSION,
            faq_html=faq_html(lang), reads_html=reads_html(lang, arts), jsonld=jsonld(lang, page),
        )
        values = {k: (v if k in ("faq_html", "reads_html", "jsonld") else html.escape(v, quote=True))
                  for k, v in values.items()}
        out = select_language(source, lang)
        out = PIXEL.sub(pixel_svg, out)
        out = PLACEHOLDER.sub(lambda m: values[m.group(1)] if m.group(1) in values else m.group(0), out)
        problems = check(out, lang)
        for problem in problems:
            print(f"FAIL {lang}: {problem}")
        failed |= bool(problems)
        page["out"].parent.mkdir(parents=True, exist_ok=True)
        page["out"].write_text(out, encoding="utf-8")
        print(f"wrote {page['out'].relative_to(ROOT)} ({len(out.encode())} bytes)")
    (ROOT / "sitemap.xml").write_text(sitemap(arts), encoding="utf-8")
    for problem in privacy_guard.scan(ROOT):
        print(f"FAIL {problem}")
        failed = True
    print("wrote sitemap.xml")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())

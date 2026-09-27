#!/usr/bin/env python3
"""Measure how much memory a session loads under each loading strategy.

Reports bytes (exact) and tokens (estimated) for four scenarios, from the
point of view of one agent:

  full     protocol 2.x style: inject rules, strategy, all shared memory, this
           agent's memory and workflow/*.md at every session start
  resident protocol 3.x startup: only the resident tier (AGENTS.md section 1)
  task     resident + the shared topic index + the topic files a task opens
  nest     every memory file in the repository (the upper bound)

Tokens come from tiktoken's o200k_base encoding when it is installed, otherwise
from a character-class estimate (about 1.05 tokens per CJK character and one
per 4.2 other characters; calibrated against o200k_base on a real bilingual
nest, median per-file error ~6%). Claude's tokenizer is not public, so treat
token counts as estimates and byte counts as exact. No dependencies required.

Usage:
  python3 scripts/maintenance/measure-context.py [--agent HOST/ID]
          [--task shared/<topic>.md ...] [--json]
"""
import argparse
import json
import re
import sys
from pathlib import Path

CJK = re.compile(r"[　-鿿가-힯＀-￯]")
SKIP_DIRS = {"outbox", "local", "comms", "archive", ".git"}
INDEX_MARKER = "<!-- nestwork:topic-index:begin -->"


def token_counter():
    try:
        import tiktoken  # optional
        enc = tiktoken.get_encoding("o200k_base")
        return (lambda text: len(enc.encode(text))), "tiktoken o200k_base"
    except Exception:
        def estimate(text):
            cjk = len(CJK.findall(text))
            return round(cjk * 1.05 + (len(text) - cjk) / 4.2)
        return estimate, "estimate (1.05/CJK char, 1/4.2 other chars)"


def read(path):
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def default_agent():
    home = Path.home()
    host_file = home / ".nestwork_host"
    for tool in ("claude", "codex", "kimi", "gemini", "hermes", "openclaw"):
        id_file = home / f".nestwork_id_{tool}"
        if host_file.is_file() and id_file.is_file():
            return f"{host_file.read_text().strip()}/{id_file.read_text().strip()}"
    return None


def scope_files(scope):
    """memory.md plus, for a topic-mode scope, every topic file under it."""
    memory = scope / "memory.md"
    files = [memory] if memory.is_file() else []
    text = read(memory) or ""
    if INDEX_MARKER in text:
        for path in sorted(scope.rglob("*.md")):
            rel = path.relative_to(scope)
            if path.name in ("memory.md", "resident.md") and len(rel.parts) == 1:
                continue
            if any(part in SKIP_DIRS or part.startswith((".", "_")) for part in rel.parts):
                continue
            files.append(path)
    return files


def topic_mode(scope):
    return INDEX_MARKER in (read(scope / "memory.md") or "")


def scenarios(root, agent, tasks):
    agent_dir = root / "agents" / agent if agent else None
    rules = root / "queen" / "agent-rules.md"
    resident = [rules, root / "shared" / "resident.md"]
    if agent_dir:
        resident.append(agent_dir / "resident.md")

    full = [rules, root / "queen" / "strategy.md", *scope_files(root / "shared")]
    if agent_dir:
        full += scope_files(agent_dir)
    full += sorted((root / "workflow").glob("*.md"))

    task = [*resident]
    if topic_mode(root / "shared"):
        task.append(root / "shared" / "memory.md")
    task += [root / t for t in tasks]

    nest = []
    for top in ("queen", "shared", "projects", "workflow", "agents"):
        for path in sorted((root / top).rglob("*.md")):
            if not any(part in SKIP_DIRS for part in path.relative_to(root).parts):
                nest.append(path)
    return {"full": full, "resident": resident, "task": task, "nest": nest}


def default_tasks(root):
    """Pick the median-size shared topic file as a representative task."""
    shared = root / "shared"
    if not topic_mode(shared):
        return []
    topics = [p for p in scope_files(shared) if p.name != "memory.md"]
    if not topics:
        return []
    topics.sort(key=lambda p: p.stat().st_size)
    return [topics[len(topics) // 2].relative_to(root).as_posix()]


def measure(paths, count):
    seen, total_bytes, total_tokens = set(), 0, 0
    for path in paths:
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        text = read(path) or ""
        total_bytes += len(text.encode("utf-8"))
        total_tokens += count(text)
    return {"files": len(seen), "bytes": total_bytes, "tokens": total_tokens}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--agent", help="HOST/AGENT-ID (default: this machine's identity files)")
    parser.add_argument("--task", action="append", default=None,
                        help="Topic file a representative task opens, relative to the nest (repeatable).")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    root = args.root.resolve()
    agent = args.agent or default_agent()
    if agent and not (root / "agents" / agent).is_dir():
        print(f"warning: agents/{agent} not found; measuring without agent files", file=sys.stderr)
        agent = None
    tasks = args.task if args.task is not None else default_tasks(root)
    missing = [t for t in tasks if not (root / t).is_file()]
    if missing:
        parser.error(f"--task file not found: {', '.join(missing)}")

    count, method = token_counter()
    results = {name: measure(paths, count) for name, paths in scenarios(root, agent, tasks).items()}
    report = {"agent": agent, "tasks": tasks, "token_method": method, "scenarios": results}

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    labels = {
        "full": "2.x-style full startup",
        "resident": "3.x startup (resident only)",
        "task": "3.x task (resident + index + topics)",
        "nest": "whole nest (upper bound)",
    }
    print(f"agent: {agent or '(none)'}   tokens: {method}")
    if tasks:
        print(f"task topics: {', '.join(tasks)}")
    print(f"{'scenario':<40}{'files':>6}{'KB':>10}{'tokens':>11}")
    for name, label in labels.items():
        r = results[name]
        print(f"{label:<40}{r['files']:>6}{r['bytes'] / 1024:>10.1f}{r['tokens']:>11,}")
    full = results["full"]["tokens"]
    for name in ("resident", "task"):
        part = results[name]["tokens"]
        if full and part:
            print(f"{labels[name]}: {part / full * 100:.1f}% of full startup ({full / part:.0f}x fewer tokens)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

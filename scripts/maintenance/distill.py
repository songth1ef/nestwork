#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# nestwork memory distiller
#
# Default mode prints an LLM-ready prompt that merges all agents/*/*/memory.md
# into a new shared/memory.md.
#
# Manual end-to-end mode runs that distillation through a local CLI agent,
# validates the result, writes shared/memory.md, and optionally commits +
# pushes it with the protocol commit message. Two runners are supported:
# `--run-claude` (claude -p) and `--run-codex` (codex exec). Pick whichever
# tool this machine is actually signed in to -- a distiller tied to a single
# vendor stops working the moment that subscription lapses.
#
# Topic mode (AGENTS.md section 6): when shared/memory.md carries the
# topic-index markers, the distiller reads and writes shared/<topic>.md files
# instead of one monolith, then regenerates the index. Rewriting a split nest
# back into a single file would undo the split on every run.
# -----------------------------------------------------------------------------

import argparse
import importlib.util
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def default_nestwork_path() -> Path:
    script_dir = Path(__file__).resolve().parent
    return script_dir.parents[1]


def read_file_robust(path: Path) -> str | None:
    """Read a file while tolerating a handful of plausible encodings."""
    for enc in ("utf-8-sig", "utf-16", "gbk", "utf-8", "latin-1"):
        try:
            return path.read_text(encoding=enc).strip()
        except (UnicodeDecodeError, UnicodeError):
            continue
    return None


def load_memory_index():
    path = Path(__file__).resolve().parent / "memory-index.py"
    spec = importlib.util.spec_from_file_location("nestwork_memory_index", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MEMORY_INDEX = load_memory_index()
REVIEW_HINT = (
    "Not committed. Review with `git diff -- shared/`, then commit with "
    "`git commit -m 'memory: distill shared' -- shared/` or rerun with --commit."
)
TOPIC_PATH = re.compile(r"^shared/[a-z0-9][a-z0-9-]*(?:/[a-z0-9][a-z0-9-]*)?\.md$")
TOPIC_BLOCK = re.compile(r"^<<<FILE (\S+)[ \t]*\r?\n(.*?)\r?\n>>>END[ \t]*$", re.S | re.M)


def is_topic_scope(scope: Path) -> bool:
    memory = scope / "memory.md"
    return memory.is_file() and MEMORY_INDEX.BEGIN in (read_file_robust(memory) or "")


def read_scope(scope: Path) -> str | None:
    """Memory of one scope: memory.md plus its topic files when split."""
    content = read_file_robust(scope / "memory.md")
    if not is_topic_scope(scope):
        return content
    parts = [content or ""]
    for path, rel in MEMORY_INDEX.topic_files(scope):
        body = read_file_robust(path)
        if body:
            parts.append(f"### Topic file `{rel.as_posix()}`\n\n{body}")
    return "\n\n".join(parts)


def collect_memory_data(nestwork_path: Path) -> list[dict[str, str]]:
    agents_dir = nestwork_path / "agents"
    if not agents_dir.exists():
        raise FileNotFoundError(f"agents/ not found at {agents_dir}")

    memory_data: list[dict[str, str]] = []
    for host_dir in sorted(agents_dir.iterdir()):
        if not host_dir.is_dir():
            continue
        for agent_dir in sorted(host_dir.iterdir()):
            if not (agent_dir / "memory.md").is_file():
                continue
            content = read_scope(agent_dir)
            if content and "_No memory yet._" not in content:
                memory_data.append(
                    {
                        "id": f"{host_dir.name}/{agent_dir.name}",
                        "content": content,
                    }
                )
    return memory_data


def build_prompt(current_shared: str, memory_data: list[dict[str, str]], now: str) -> str:
    sources = ", ".join(f"`{item['id']}`" for item in memory_data)

    sections = [
        "--- DISTILLATION PROMPT BEGIN ---",
        f"Date: {now}",
        "",
        "# TASK: Distill Agent Memories into Shared Memory",
        "",
        "You are the Nestwork distiller. Your goal is to merge individual "
        "agent observations into the central `shared/memory.md` according to "
        "the protocol in `AGENTS.md` section 7.",
        "",
        "## Rules:",
        "1. Merge cross-agent stable facts (user identity, tech stack, preferences).",
        "2. Keep divergent observations if they are consistent (different machines / tools).",
        "3. Filter out temporary task details or one-off debugging notes.",
        "4. NEVER delete facts from shared memory; only add, update, or unify.",
        "5. Keep the Markdown clean and readable.",
        "6. Preserve the shared-memory header, refresh `Last compiled`, and include a `Sources` line.",
        "",
        f"## Source agents ({len(memory_data)}): {sources}",
        "",
        "## Current shared/memory.md:",
        "```markdown",
        current_shared if current_shared else "(Empty)",
        "```",
    ]

    for memory in memory_data:
        sections.extend(
            [
                "",
                f"## Private memory from agent: {memory['id']}",
                "```markdown",
                memory["content"],
                "```",
            ]
        )

    sections.extend(
        [
            "",
            "## Instruction:",
            "Analyze the content above. Output the FULL contents for the new "
            "`shared/memory.md`. Wrap your output in a single markdown block.",
            "--- DISTILLATION PROMPT END ---",
        ]
    )
    return "\n".join(sections) + "\n"


def read_shared_topics(nestwork_path: Path) -> dict[str, str]:
    shared = nestwork_path / "shared"
    return {
        f"shared/{rel.as_posix()}": read_file_robust(path) or ""
        for path, rel in MEMORY_INDEX.topic_files(shared)
    }


def build_topic_prompt(topics: dict[str, str], memory_data: list[dict[str, str]], now: str) -> str:
    sources = ", ".join(f"`{item['id']}`" for item in memory_data)
    sections = [
        "--- DISTILLATION PROMPT BEGIN ---",
        f"Date: {now}",
        "",
        "# TASK: Distill Agent Memories into Shared Topic Files",
        "",
        "You are the Nestwork distiller. Shared memory is split into topic "
        "files under `shared/` (AGENTS.md sections 6 and 7). Each topic file "
        "starts with YAML front matter whose `description` says when an agent "
        "should read it; agents choose files by that line alone.",
        "",
        "## Rules:",
        "1. Merge cross-agent stable facts into the existing topic that fits best.",
        "2. Create a new topic only when no existing description covers the fact. "
        "Never rename, merge or delete topics; that needs human review.",
        "3. Keep divergent observations if they are consistent (different machines / tools).",
        "4. Filter out temporary task details or one-off debugging notes.",
        "5. NEVER delete facts; only add, update, or unify. Keep provenance dates.",
        "6. Every file keeps front matter with `description` (one line, when to read) "
        f"and `updated: {now[:10]}` when changed.",
        "",
        f"## Source agents ({len(memory_data)}): {sources}",
        "",
        "## Current shared topic files:",
    ]
    for name, body in topics.items():
        sections.extend(["", f"<<<FILE {name}", body, ">>>END"])
    if not topics:
        sections.append("(None yet)")

    for memory in memory_data:
        sections.extend(
            [
                "",
                f"## Private memory from agent: {memory['id']}",
                "```markdown",
                memory["content"],
                "```",
            ]
        )

    sections.extend(
        [
            "",
            "## Instruction:",
            "Output ONLY the topic files that change or are new, each as its FULL "
            "contents between a `<<<FILE shared/<topic>.md` line and a `>>>END` "
            "line. Paths are lowercase kebab-case, at most one subfolder deep. "
            "Do not output shared/memory.md or shared/resident.md.",
            "--- DISTILLATION PROMPT END ---",
        ]
    )
    return "\n".join(sections) + "\n"


def extract_topic_files(text: str) -> dict[str, str]:
    files: dict[str, str] = {}
    for match in TOPIC_BLOCK.finditer(text):
        name, body = match.group(1), match.group(2).strip()
        if not TOPIC_PATH.match(name) or name.endswith(("/memory.md", "/resident.md")):
            raise ValueError(f"distiller proposed an invalid topic path: {name}")
        if not MEMORY_INDEX.parse_front_matter(body + "\n").get("description"):
            raise ValueError(f"{name}: missing `description` front matter")
        files[name] = body + "\n"
    if not files:
        raise ValueError("LLM output contained no <<<FILE ... >>>END topic blocks")
    return files


def extract_shared_memory(text: str) -> str:
    fence_pattern = re.compile(r"```(?:markdown|md)?\r?\n(.*?)```", re.S | re.I)
    candidates = [match.group(1).strip() for match in fence_pattern.finditer(text)]

    for candidate in candidates:
        if candidate.startswith("# SHARED MEMORY"):
            return candidate.rstrip() + "\n"

    raw = text.strip()
    if raw.startswith("# SHARED MEMORY"):
        return raw.rstrip() + "\n"

    for candidate in candidates:
        if "# SHARED MEMORY" in candidate:
            return candidate.rstrip() + "\n"

    raise ValueError("LLM output did not contain a markdown block for shared/memory.md")


def validate_shared_memory(content: str) -> list[str]:
    warnings: list[str] = []
    if not content.lstrip().startswith("# SHARED MEMORY"):
        warnings.append("missing `# SHARED MEMORY` header")
    line_count = len(content.splitlines())
    if line_count > 500:
        warnings.append(f"shared/memory.md exceeds 500 lines ({line_count})")
    return warnings


def run_claude(prompt: str, model: str | None) -> str:
    claude = shutil.which("claude")
    if not claude:
        raise FileNotFoundError("`claude` executable not found in PATH")

    with tempfile.TemporaryDirectory(prefix="nestwork-distill-") as tmp:
        cmd = [
            claude,
            "-p",
            # Pure text distillation: no tools, and no user/project settings, so
            # a CLAUDE.md startup protocol cannot hijack the output. Without
            # this the distiller obeys the nest's own bootstrap and answers with
            # a session-start summary instead of a shared/memory.md candidate.
            "--tools",
            "",
            "--setting-sources",
            "",
        ]
        if model:
            cmd += ["--model", model]

        result = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            # Agent memory is routinely non-ASCII, and `text=True` alone decodes
            # with the *locale* codec -- on a zh-CN Windows box that is GBK, and
            # the whole run dies with UnicodeDecodeError before the distilled
            # memory is ever parsed. Pin UTF-8 in both directions.
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            cwd=tmp,
        )
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            detail = f"\n--- claude stderr ---\n{stderr}" if stderr else ""
            raise RuntimeError(f"claude -p failed (exit {result.returncode}).{detail}")
        return result.stdout


def run_codex(prompt: str, profile: str | None, model: str | None) -> str:
    codex = shutil.which("codex")
    if not codex:
        raise FileNotFoundError("`codex` executable not found in PATH")

    with tempfile.TemporaryDirectory(prefix="nestwork-distill-") as tmp:
        tmp_path = Path(tmp)
        output_path = tmp_path / "codex-last-message.md"
        cmd = [
            codex,
            "exec",
            "-C",
            str(tmp_path),
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "--ephemeral",
            "--ignore-rules",
            "--output-last-message",
            str(output_path),
            "-",
        ]
        if profile:
            cmd[2:2] = ["--profile", profile]
        if model:
            cmd[2:2] = ["--model", model]

        result = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            # Same reason as run_claude: locale-codec decoding of non-ASCII
            # memory turns into UnicodeDecodeError on non-UTF-8 Windows locales.
            encoding="utf-8",
            errors="replace",
            capture_output=True,
        )
        if result.returncode != 0:
            # Surface codex's own stderr: the bare CalledProcessError string
            # hides it, and flag mismatches across Codex CLI versions are the
            # most likely failure here.
            stderr = (result.stderr or "").strip()
            detail = f"\n--- codex stderr ---\n{stderr}" if stderr else ""
            raise RuntimeError(
                f"codex exec failed (exit {result.returncode}). If stderr "
                "mentions an unknown flag, your Codex CLI version may not "
                f"support the flags used here: {' '.join(cmd[1:])}{detail}"
            )
        return output_path.read_text(encoding="utf-8")


def run_git(nestwork_path: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(nestwork_path), *args],
        text=True,
        capture_output=True,
        check=check,
    )


def write_shared_memory(
    nestwork_path: Path,
    shared_content: str,
    *,
    commit: bool,
    push: bool,
) -> None:
    shared_path = nestwork_path / "shared" / "memory.md"
    if commit:
        run_git(nestwork_path, "pull", "--rebase", "--autostash", "-q")

    shared_path.write_text(shared_content, encoding="utf-8")
    if not commit:
        return

    run_git(nestwork_path, "add", "shared/memory.md")

    diff = run_git(nestwork_path, "diff", "--cached", "--quiet", "--", "shared/memory.md", check=False)
    if diff.returncode == 0:
        return
    if diff.returncode != 1:
        raise subprocess.CalledProcessError(
            diff.returncode,
            diff.args,
            output=diff.stdout,
            stderr=diff.stderr,
        )

    run_git(nestwork_path, "commit", "-m", "memory: distill shared", "--", "shared/memory.md")
    if push:
        run_git(nestwork_path, "push", "-q")


def write_topic_files(
    nestwork_path: Path,
    files: dict[str, str],
    *,
    commit: bool,
    push: bool,
) -> None:
    if commit:
        run_git(nestwork_path, "pull", "--rebase", "--autostash", "-q")

    for name, body in files.items():
        path = nestwork_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    shared = nestwork_path / "shared"
    if MEMORY_INDEX.process(nestwork_path, shared, check=False):
        raise ValueError("shared topic index has problems; fix them before committing")
    if not commit:
        return

    run_git(nestwork_path, "add", "--", "shared/")
    diff = run_git(nestwork_path, "diff", "--cached", "--quiet", "--", "shared/", check=False)
    if diff.returncode == 0:
        return
    if diff.returncode != 1:
        raise subprocess.CalledProcessError(diff.returncode, diff.args, output=diff.stdout, stderr=diff.stderr)

    run_git(nestwork_path, "commit", "-m", "memory: distill shared", "--", "shared/")
    if push:
        run_git(nestwork_path, "push", "-q")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print or run a manual all-agent memory distillation into shared/memory.md."
    )
    parser.add_argument(
        "--nestwork-path",
        default=str(default_nestwork_path()),
        help="Path to the Nestwork repository. Defaults to the repo that contains this script.",
    )
    parser.add_argument(
        "--run-claude",
        action="store_true",
        help="Run the distillation end-to-end with `claude -p`, then write shared/memory.md.",
    )
    parser.add_argument(
        "--run-codex",
        action="store_true",
        help="Run the distillation end-to-end with `codex exec`, then write shared/memory.md.",
    )
    parser.add_argument(
        "--profile",
        default=os.environ.get("NESTWORK_DISTILL_CODEX_PROFILE", ""),
        help="Optional `codex exec --profile` value for --run-codex (Codex only).",
    )
    parser.add_argument(
        "--model",
        default="",
        help="Optional model override for the selected runner. Defaults to "
        "$NESTWORK_DISTILL_CLAUDE_MODEL / $NESTWORK_DISTILL_CODEX_MODEL.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the distiller and print the candidate shared/memory.md instead of writing it.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="After writing, create the `memory: distill shared` commit and push it. "
        "Without this flag the result is only written to the working tree, so a human "
        "can review it first (AGENTS.md section 7).",
    )
    parser.add_argument(
        "--no-commit",
        action="store_true",
        help="Accepted for compatibility; not committing is already the default.",
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="With --commit: commit locally but skip `git push`.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    # Writing shared memory skips the review step unless a human looks first, so
    # committing is opt-in (AGENTS.md section 7, steps 3-4).
    commit = args.commit and not args.no_commit
    nestwork_path = Path(args.nestwork_path).resolve()
    shared_file = nestwork_path / "shared" / "memory.md"

    try:
        memory_data = collect_memory_data(nestwork_path)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not memory_data:
        print("No meaningful agent memory found to distill.")
        return 0

    topic_mode = is_topic_scope(nestwork_path / "shared")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if topic_mode:
        prompt = build_topic_prompt(read_shared_topics(nestwork_path), memory_data, now)
    else:
        current_shared = read_file_robust(shared_file) or ""
        prompt = build_prompt(current_shared, memory_data, now)

    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    if args.run_claude and args.run_codex:
        print("Error: --run-claude and --run-codex are mutually exclusive.", file=sys.stderr)
        return 2

    if not (args.run_claude or args.run_codex):
        print(prompt, end="")
        return 0

    if args.run_claude and args.profile:
        print("Warning: --profile applies to --run-codex only; ignoring.", file=sys.stderr)

    try:
        if args.run_claude:
            model = args.model or os.environ.get("NESTWORK_DISTILL_CLAUDE_MODEL", "")
            raw_output = run_claude(prompt, model or None)
        else:
            model = args.model or os.environ.get("NESTWORK_DISTILL_CODEX_MODEL", "")
            raw_output = run_codex(prompt, args.profile or None, model or None)
        if topic_mode:
            topic_files = extract_topic_files(raw_output)
        else:
            shared_content = extract_shared_memory(raw_output)
    except (FileNotFoundError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if topic_mode:
        if args.dry_run:
            for name, body in topic_files.items():
                print(f"<<<FILE {name}\n{body}>>>END")
            return 0
        try:
            write_topic_files(nestwork_path, topic_files, commit=commit, push=not args.no_push)
        except (ValueError, subprocess.CalledProcessError) as exc:
            stderr = getattr(exc, "stderr", None)
            print(f"Error: {stderr.strip() if stderr else exc}", file=sys.stderr)
            return 1
        print(f"Updated {len(topic_files)} shared topic file(s): {', '.join(topic_files)}")
        if commit:
            print("Committed" + ("" if args.no_push else " and pushed") + ": memory: distill shared")
        else:
            print(REVIEW_HINT)
        return 0

    for warning in validate_shared_memory(shared_content):
        print(f"Warning: {warning}", file=sys.stderr)

    if args.dry_run:
        print(shared_content, end="")
        return 0

    try:
        write_shared_memory(
            nestwork_path,
            shared_content,
            commit=commit,
            push=not args.no_push,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else str(exc)
        print(f"Error: {stderr}", file=sys.stderr)
        return 1

    print(f"Updated {shared_file}")
    if commit:
        if args.no_push:
            print("Committed local change with message: memory: distill shared")
        else:
            print("Committed and pushed: memory: distill shared")
    else:
        print(REVIEW_HINT)
    return 0


if __name__ == "__main__":
    sys.exit(main())

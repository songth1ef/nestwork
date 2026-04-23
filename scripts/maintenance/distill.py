#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# nestwork memory distiller
#
# Default mode prints an LLM-ready prompt that merges all agents/*/*/memory.md
# into a new shared/memory.md.
#
# Manual end-to-end mode (`--run-codex`) uses codex exec to run that
# distillation, validates the result, writes shared/memory.md, and optionally
# commits + pushes it with the protocol commit message.
# -----------------------------------------------------------------------------

import argparse
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


def collect_memory_data(nestwork_path: Path) -> list[dict[str, str]]:
    agents_dir = nestwork_path / "agents"
    if not agents_dir.exists():
        raise FileNotFoundError(f"agents/ not found at {agents_dir}")

    memory_data: list[dict[str, str]] = []
    for host_dir in sorted(agents_dir.iterdir()):
        if not host_dir.is_dir():
            continue
        for agent_dir in sorted(host_dir.iterdir()):
            memory_path = agent_dir / "memory.md"
            if not memory_path.is_file():
                continue
            content = read_file_robust(memory_path)
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

    raise ValueError("Codex output did not contain a markdown block for shared/memory.md")


def validate_shared_memory(content: str) -> list[str]:
    warnings: list[str] = []
    if not content.lstrip().startswith("# SHARED MEMORY"):
        warnings.append("missing `# SHARED MEMORY` header")
    line_count = len(content.splitlines())
    if line_count > 500:
        warnings.append(f"shared/memory.md exceeds 500 lines ({line_count})")
    return warnings


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
            "--output-last-message",
            str(output_path),
            "-",
        ]
        if profile:
            cmd[2:2] = ["--profile", profile]
        if model:
            cmd[2:2] = ["--model", model]

        subprocess.run(
            cmd,
            input=prompt,
            text=True,
            capture_output=True,
            check=True,
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
        "--run-codex",
        action="store_true",
        help="Run the distillation end-to-end with `codex exec`, then write shared/memory.md.",
    )
    parser.add_argument(
        "--profile",
        default=os.environ.get("NESTWORK_DISTILL_CODEX_PROFILE", ""),
        help="Optional `codex exec --profile` value for --run-codex.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("NESTWORK_DISTILL_CODEX_MODEL", ""),
        help="Optional `codex exec --model` value for --run-codex.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run Codex and print the candidate shared/memory.md instead of writing it.",
    )
    parser.add_argument(
        "--no-commit",
        action="store_true",
        help="Write shared/memory.md without creating the `memory: distill shared` commit.",
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Commit locally but skip `git push`.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
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

    current_shared = read_file_robust(shared_file) or ""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    prompt = build_prompt(current_shared, memory_data, now)

    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    if not args.run_codex:
        print(prompt, end="")
        return 0

    try:
        raw_output = run_codex(prompt, args.profile or None, args.model or None)
        shared_content = extract_shared_memory(raw_output)
    except (FileNotFoundError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    for warning in validate_shared_memory(shared_content):
        print(f"Warning: {warning}", file=sys.stderr)

    if args.dry_run:
        print(shared_content, end="")
        return 0

    try:
        write_shared_memory(
            nestwork_path,
            shared_content,
            commit=not args.no_commit,
            push=not args.no_push,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else str(exc)
        print(f"Error: {stderr}", file=sys.stderr)
        return 1

    print(f"Updated {shared_file}")
    if not args.no_commit:
        if args.no_push:
            print("Committed local change with message: memory: distill shared")
        else:
            print("Committed and pushed: memory: distill shared")
    return 0


if __name__ == "__main__":
    sys.exit(main())

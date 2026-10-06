#!/usr/bin/env python3
"""nestwork x Antigravity -- PreInvocation hook (session start).

Fires before model invocations in Antigravity CLI / IDE / 2.0.
Deduplicates per conversationId so it only executes on session start:
  1. git pull --rebase the nest (with autostash and branch guard)
  2. generates local/recent.md (Protocol 3.2 digest) and agent inbox snapshot
  3. injects an ephemeral system message with the tiered context manifest
     (resident files first, on-demand as needed).

Contract: JSON on stdin, JSON on stdout ({} = no-op).
"""

import json
import os
import subprocess
import sys


def git_cmd(nest: str, *args: str, timeout: int = 20) -> tuple[int, str]:
    try:
        r = subprocess.run(
            ["git", "-C", nest, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as e:  # noqa: BLE001
        return 1, str(e)


def is_locked(nest: str) -> bool:
    try:
        agents_path = os.path.join(nest, "AGENTS.md")
        if os.path.exists(agents_path):
            with open(agents_path, "rb") as f:
                return f.read(10).startswith(b"\x00GITCRYPT")
        return False
    except OSError:
        return False


def main() -> None:
    if len(sys.argv) < 4:
        print("{}")
        return

    nest = sys.argv[1]
    host = sys.argv[2]
    aid = sys.argv[3]

    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        payload = {}
    conv = payload.get("conversationId") or "unknown"

    home_dir = os.environ.get("ANTIGRAVITY_HOME") or os.environ.get("GEMINI_HOME") or os.path.expanduser("~/.gemini")
    state_dir = os.path.join(home_dir, "config", "nestwork", "state")
    os.makedirs(state_dir, exist_ok=True)
    marker = os.path.join(state_dir, conv)
    if os.path.exists(marker):
        print("{}")
        return
    try:
        with open(marker, "w") as f:
            f.write("")
    except OSError:
        pass

    if not os.path.isdir(os.path.join(nest, ".git")):
        msg = f"[nestwork] Nest repo not found at {nest}. Tell the user nestwork is not available this session."
        print(json.dumps({"injectSteps": [{"ephemeralMessage": msg}]}))
        return

    # Branch guard: verify checkout is on the default branch
    branch_warning = ""
    rc_curr, curr_branch = git_cmd(nest, "symbolic-ref", "-q", "--short", "HEAD")
    rc_orig, orig_head = git_cmd(nest, "symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD")
    def_branch = orig_head.replace("origin/", "") if rc_orig == 0 else ""
    if def_branch and curr_branch and curr_branch != def_branch:
        branch_warning = (
            f"[!] Nestwork checkout is on '{curr_branch}', not '{def_branch}': "
            f"context below may not be this instance's; pull skipped. Tell the user; "
            f"fix with: git -C {nest} switch {def_branch}\n"
        )
    else:
        rc, out = git_cmd(nest, "pull", "--rebase", "--autostash", "-q")
        if rc != 0:
            git_cmd(nest, "rebase", "--abort")

    if is_locked(nest):
        msg = (
            f"[nestwork] Nest at {nest} is git-crypt LOCKED. "
            "Protocol files are unreadable. Tell the user once that the git-crypt key is needed "
            f"(`git -C {nest} crypt unlock <key>`), then proceed normally. "
            "Do NOT write or commit anything into the nest while locked."
        )
        print(json.dumps({"injectSteps": [{"ephemeralMessage": msg}]}))
        return

    # Generate recent-activity digest (Protocol 3.2)
    digest_script = os.path.join(nest, "scripts", "maintenance", "recent-digest.py")
    recent_rel = "local/recent.md"
    recent_full = os.path.join(nest, recent_rel)
    if os.path.isfile(digest_script):
        try:
            subprocess.run(
                [sys.executable, digest_script, "--nest", nest, "--out", recent_full],
                capture_output=True,
                timeout=15,
            )
        except Exception:  # noqa: BLE001
            pass

    # Inbox refresh
    read_sh = os.path.join(nest, "scripts", "comms", "read.sh")
    inbox_rel = f"agents/{host}/{aid}/local/inbox.md"
    inbox_full = os.path.join(nest, inbox_rel)
    if os.path.isfile(read_sh) and os.name != "nt":
        env = os.environ.copy()
        env["NESTWORK_SELF"] = f"{host}/{aid}"
        try:
            subprocess.run(
                ["bash", read_sh, "--write", inbox_full],
                env=env,
                capture_output=True,
                timeout=10,
            )
        except Exception:  # noqa: BLE001
            pass

    resident_files = [
        "queen/agent-rules.md",
        "shared/resident.md",
        f"agents/{host}/{aid}/resident.md",
        recent_rel,
    ]
    manifest_lines = []
    for rel in resident_files:
        full = os.path.join(nest, rel)
        if os.path.isfile(full):
            manifest_lines.append(f"- {full}")

    on_demand_lines = [
        f"- {nest}/queen/strategy.md",
        f"- {nest}/shared/memory.md",
        f"- {nest}/agents/{host}/{aid}/memory.md",
    ]
    if os.path.isfile(inbox_full):
        on_demand_lines.append(f"- {inbox_full}")
    on_demand_lines.append(f"- {nest}/projects/ and {nest}/workflow/ (select by task)")

    resident_block = "\n".join(manifest_lines)
    on_demand_block = "\n".join(on_demand_lines)

    msg = f"""[nestwork] NESTWORK BOOTSTRAP — you are agent `{host}/{aid}` (Antigravity).
{branch_warning}
=== READ-ON-START (resident files only) ===
{resident_block}

=== READ-ON-DEMAND (search relevant sections, do not load all) ===
{on_demand_block}
Full protocol: {nest}/AGENTS.md

Write protocol: ordinary memory writes belong only in {nest}/agents/{host}/{aid}/.
A Stop hook auto-commits and pushes that directory when the turn ends.
"""
    print(json.dumps({"injectSteps": [{"ephemeralMessage": msg}]}))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"nestwork antigravity session_start error: {e}\n")
        print("{}")

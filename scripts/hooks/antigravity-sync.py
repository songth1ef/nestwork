#!/usr/bin/env python3
"""nestwork x Antigravity -- Stop hook (memory sync).

When the agent turn terminates, commit + push this agent's directory
(agents/<host>/<agent-id>/) if it changed.

Safety: refuses to commit if git-crypt is locked or unconfigured, so
plaintext is never pushed to an encrypted-at-rest repo.
Throttles high-frequency local/ only changes to local_commit_min_interval_sec.
Always outputs {} (never blocks agent completion).
"""

import json
import os
import random
import subprocess
import sys
import time


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


def crypt_safe(nest: str) -> bool:
    agents_path = os.path.join(nest, "AGENTS.md")
    if os.path.exists(agents_path):
        try:
            with open(agents_path, "rb") as f:
                if f.read(10).startswith(b"\x00GITCRYPT"):
                    return False
        except OSError:
            return False

    if os.path.isdir(os.path.join(nest, ".git", "git-crypt")):
        rc, _ = git_cmd(nest, "config", "--get", "filter.git-crypt.clean")
        if rc != 0:
            return False
    return True


def read_setting_int(nest: str, host: str, key: str, default: int) -> int:
    settings_file = os.path.join(nest, "agents", host, "settings.json")
    if not os.path.isfile(settings_file):
        return default
    try:
        with open(settings_file, "r", encoding="utf-8") as f:
            val = json.load(f).get(key, default)
            return int(val)
    except Exception:  # noqa: BLE001
        return default


def main() -> None:
    if len(sys.argv) < 4:
        print("{}")
        return

    nest = sys.argv[1]
    host = sys.argv[2]
    aid = sys.argv[3]

    try:
        json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        pass

    rel = f"agents/{host}/{aid}/"
    full_path = os.path.join(nest, rel)

    if not os.path.isdir(full_path) or not crypt_safe(nest):
        print("{}")
        return

    git_cmd(nest, "add", rel)
    rc, _ = git_cmd(nest, "diff", "--cached", "--quiet", "--", rel)
    if rc == 0:
        print("{}")
        return

    # Check throttle if only files under local/ changed
    local_rel = f"{rel}local/"
    rc_diff, diff_files = git_cmd(
        nest, "diff", "--cached", "--name-only", "--", rel, f":(exclude){local_rel}*"
    )
    if not diff_files.strip():
        interval = read_setting_int(nest, host, "local_commit_min_interval_sec", 3600)
        rc_ts, last_ts = git_cmd(nest, "log", "-1", "--format=%ct", "--", local_rel)
        if rc_ts == 0 and last_ts.strip().isdigit():
            elapsed = int(time.time()) - int(last_ts.strip())
            if elapsed < interval:
                git_cmd(nest, "reset", "-q", "HEAD", "--", local_rel)
                print("{}")
                return

    commit_msg = f"memory: update {host}/{aid}"
    rc, _ = git_cmd(nest, "commit", "-m", commit_msg, "--", rel)
    if rc != 0:
        print("{}")
        return

    # Push with backoff and retry (up to 3 attempts)
    for attempt in range(1, 4):
        rc, _ = git_cmd(nest, "push", "-q")
        if rc == 0:
            print("{}")
            return
        sleep_sec = (2 ** (attempt - 1)) * 0.5 + random.uniform(0.0, 0.3)
        time.sleep(sleep_sec)
        git_cmd(nest, "reset", "--soft", "HEAD~1")
        rc_pull, _ = git_cmd(nest, "pull", "--rebase", "--autostash", "-q")
        if rc_pull != 0:
            git_cmd(nest, "rebase", "--abort")
            break
        git_cmd(nest, "commit", "-m", commit_msg, "--", rel)

    print("{}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"nestwork antigravity sync error: {e}\n")
        print("{}")

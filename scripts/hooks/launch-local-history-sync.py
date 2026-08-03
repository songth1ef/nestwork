#!/usr/bin/env python3
"""Detach local-history sync so Codex SessionEnd can return within 3 seconds."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def resolve_bash() -> str:
    override = os.environ.get("NESTWORK_GIT_BASH")
    if override and Path(override).is_file():
        return override

    if os.name == "nt":
        try:
            exec_path = Path(
                subprocess.check_output(
                    ["git", "--exec-path"], text=True, stderr=subprocess.DEVNULL
                ).strip()
            )
            candidate = exec_path.parents[2] / "bin" / "bash.exe"
            if candidate.is_file():
                return str(candidate)
        except (OSError, subprocess.SubprocessError, IndexError):
            pass

        for candidate in (
            Path(os.environ.get("ProgramFiles", "C:/Program Files"))
            / "Git/bin/bash.exe",
            Path(os.environ.get("LOCALAPPDATA", ""))
            / "Programs/Git/bin/bash.exe",
        ):
            if candidate.is_file():
                return str(candidate)
        raise FileNotFoundError(
            "Git Bash not found; set NESTWORK_GIT_BASH to bash.exe"
        )

    bash = shutil.which("bash")
    if not bash:
        raise FileNotFoundError("bash not found")
    return bash


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "usage: launch-local-history-sync.py <nestwork_path> <host> <agent_id>",
            file=sys.stderr,
        )
        return 2

    nestwork_path, host, agent_id = sys.argv[1:]
    script = Path(nestwork_path) / "scripts/hooks/sync-local-history.sh"
    log_path = Path(tempfile.gettempdir()) / "nestwork-codex-session-end-hook.log"

    popen_kwargs: dict[str, object] = {
        "stdin": subprocess.DEVNULL,
        "close_fds": True,
    }
    if os.name == "nt":
        popen_kwargs["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP
            | subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NO_WINDOW
        )
    else:
        popen_kwargs["start_new_session"] = True

    try:
        with log_path.open("ab") as log:
            subprocess.Popen(
                [resolve_bash(), str(script), host, agent_id],
                stdout=log,
                stderr=subprocess.STDOUT,
                **popen_kwargs,
            )
    except OSError as error:
        print(f"nestwork local-history sync launch failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

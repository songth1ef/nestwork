#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# nestwork bootstrap remover (shared by uninstall-claude / uninstall-gemini /...)
#
# Inverse of scripts/install/_bootstrap.py: deletes the nestwork marker block
# (current and legacy marker names) from a tool-specific markdown file while
# preserving every byte of user content outside the markers.
#
# Behaviour:
#   - File does not exist            -> no-op
#   - Markers present                -> remove block (plus surrounding blank run)
#   - File empty after removal       -> delete the file (installer created it)
#   - No markers                     -> no-op, report "not installed"
#
# Never touches agents/<host>/<id>/ memory or identity files.
#
# Usage:
#   _unbootstrap.py <target_md>
# -----------------------------------------------------------------------------

import os
import re
import sys

BEGIN = "<!-- nestwork:begin -->"
END   = "<!-- nestwork:end -->"
LEGACY_BEGIN = "<!-- " + "hive" + "queen:begin -->"
LEGACY_END = "<!-- " + "hive" + "queen:end -->"


def strip_block(content: str, begin: str, end: str) -> tuple[str, bool]:
    pattern = re.compile(
        r"[ \t]*" + re.escape(begin) + r".*?" + re.escape(end) + r"[ \t]*\n?",
        re.DOTALL,
    )
    stripped, count = pattern.subn("", content)
    if count:
        # Collapse the blank run left where the block used to sit.
        stripped = re.sub(r"\n{3,}", "\n\n", stripped)
    return stripped, bool(count)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: _unbootstrap.py <target_md>", file=sys.stderr)
        return 2

    target = sys.argv[1]
    if not os.path.exists(target):
        print(f"nestwork bootstrap: {target} does not exist (nothing to remove)")
        return 0

    with open(target, encoding="utf-8") as f:
        content = f.read()

    content, removed = strip_block(content, BEGIN, END)
    content, removed_legacy = strip_block(content, LEGACY_BEGIN, LEGACY_END)

    if not (removed or removed_legacy):
        print(f"nestwork bootstrap: no marker block in {target} (nothing to remove)")
        return 0

    if not content.strip():
        os.remove(target)
        print(f"nestwork bootstrap removed; deleted now-empty {target}")
    else:
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"nestwork bootstrap removed from {target} (user content preserved)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

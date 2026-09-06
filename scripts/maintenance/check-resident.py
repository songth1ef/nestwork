#!/usr/bin/env python3
"""Report UTF-8 resident file sizes; nonzero for missing rules or over budget."""
import argparse
from pathlib import Path


def check(root):
    files = [(root / 'queen/agent-rules.md', 4096, True),
             (root / 'shared/resident.md', 4096, False)]
    files.extend((p, 2048, False) for p in sorted(root.glob('agents/*/*/resident.md')))
    failures = 0
    for path, budget, required in files:
        if not path.exists():
            if required:
                print(f'MISSING {path.relative_to(root)}')
                failures += 1
            continue
        size = path.stat().st_size
        failed = size > budget
        failures += failed
        print(f'{"OVER" if failed else "OK"} {path.relative_to(root)}: {size}/{budget} bytes')
    return int(failures > 0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    raise SystemExit(check(args.root.resolve()))

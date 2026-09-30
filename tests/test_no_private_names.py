"""Public-repo guard: no real host, agent, employer or private-repo names.

This template ships publicly, and examples copied from a working instance are
the usual way a real hostname or project name slips in. The list below holds
only SHA-256 hashes of lowercased tokens, so the guard does not republish the
names it blocks. Each token found in a tracked text file is checked whole and
split on `-`, `_` and `.`.

Instance owners can add plaintext names that never leave their machine in
~/.config/nestwork/private-names.txt (one per line), or point
NESTWORK_PRIVATE_NAMES at another file.
"""
import hashlib
import os
import re
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BLOCKED_SHA256 = {
    "0e034f278cd9a66d6c1cecbd8a9cd9e44658cc1dba30eae317631bf12739be09",
    "12c18ee887b05acff6ad4a75f5f55dfd383320259099dbcfb62db54902499f39",
    "188c78aed70e4b3be890da7342d49d33c217a562627ecff356bff2ae7276f3e2",
    "240bb423a39007ce080fef48f773303794c58c2c6d849f25bf203e2d150e7bb6",
    "4a090e13b8c5c7976d6c0cb4e9751d8e8dcb10fde8b87ffe1d66a26a06cc1773",
    "4a65865de772e55341c2b49d94a3a4b4c916143ab8e2ad6e48ef58774a86f34d",
    "4d5c13af87c82178f68e955dde031b73a20a61417f2292ca5edb9a0072b04e66",
    "5ef5f655949490f572a2e67f7d7332945a2107ed712e20edefee44f550d8e207",
    "6da0039598038673212aa275d15374252fc384eaf668c4a9615d11746ac4fd33",
    "6da00c99a0b8af41e0cc4e6871f750bc2a8667a3fcff045eda433503a3d674dc",
    "6e4f223a6ead62ebd88cb45cfc917e4dc7c36874e26ca635c0053336cb05e984",
    "77425294aaa7a555059424fcd8861f4bff836fa1e81cffabe729a224880fa236",
    "7aae4d3a8bcb6eea2f881a3bd6e3df857c966004740c831e9ef9e2c1ee0aeabd",
    "7e69d6f35ad64eb7ee1c8dea550c4432a93024c1a0c012531f63b4f18936be6c",
    "831a4eb363957a7da1fe31ca50be84d7fdbd58cb690b20c62d83babc1cc0b296",
    "8b9217d789ce7d081678d3f4cbcc7a75c523fb0d8328ff3c7ecc5bf290a43c18",
    "8d0d522814b642f384980bc73e4c5c094a64eaa489b04ffd464ead508887570c",
    "930d7ee08d80de53ae0f4caf40078a49605dcbc50e17b097dc18b149f1aa3a3d",
    "93e1ab59af9d692edea60d7b3d094fa3e0057ee7b52b08aeb50228eb8c1e7671",
    "94796adbf26dc5decfce8e198ef805b3593f435875b5b60fb4d05ec25f9ec117",
    "a151618f78def3ab58c3fff02e3717c480ae8c72d40c63b333e0ed9a2b5f9319",
    "a7d201094c181d9eda50911df8a2d74bd99fb5171016883fa1249920aff9df03",
    "ae2162b9e141a523511caadb2013b7a8281c34216c79a78658eadefe58568e3d",
    "bc410c07c1bb54c64ffb783ab4cd3fec6c03533e1048f3b79b2f53a84a146617",
    "cae98aa3b171a85f4c427cb47ad57c19ddbf75b82cef3e8e31391b32e163b351",
    "d23e1e93df72441d1cdc887981834b8336b4e600688d2487e72bcb7324272ac5",
    "e241cf88206c0e2933326fd494e0a9baeffd62f8032e3519840832404f5c0336",
    "f4e11fcbc7012a492036f1be92650fe8ad1fa7f195fe7bb275be1f6d22169da5",
}
TOKEN = re.compile(r"[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*")
BINARY = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".woff", ".woff2", ".pyc")


def digest(token):
    return hashlib.sha256(token.lower().encode()).hexdigest()


def local_names():
    path = Path(os.environ.get("NESTWORK_PRIVATE_NAMES", Path.home() / ".config/nestwork/private-names.txt"))
    if not path.is_file():
        return set()
    return {line.strip().lower() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")}


def tracked_files():
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "ls-files", "-z"], capture_output=True, text=True, check=True).stdout
    return [REPO_ROOT / p for p in out.split("\0") if p and not p.endswith(BINARY)]


def violations(text, blocked_hashes, plain):
    found = set()
    for match in TOKEN.finditer(text):
        token = match.group(0)
        pieces = {token} | set(re.split(r"[._-]", token))
        for piece in pieces:
            if piece and (digest(piece) in blocked_hashes or piece.lower() in plain):
                found.add(piece)
    lowered = text.lower()
    found |= {name for name in plain if not TOKEN.fullmatch(name) and name in lowered}
    return found


class NoPrivateNamesTests(unittest.TestCase):
    def test_guard_detects_blocked_tokens(self):
        # Self-check with a throwaway hash so the real names never appear here.
        probe = {digest("example-private-host")}
        self.assertEqual(violations("see agents/example-private-host/claude-x/", probe, set()), {"example-private-host"})
        self.assertEqual(violations("no match here", probe, set()), set())
        self.assertEqual(violations("code at acme-corp/app", set(), {"acme"}), {"acme"})

    def test_tracked_files_contain_no_private_names(self):
        plain = local_names()
        report = []
        for path in tracked_files():
            if path.name == Path(__file__).name:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            hits = violations(text, BLOCKED_SHA256, plain)
            if hits:
                report.append(f"{path.relative_to(REPO_ROOT)}: {sorted(hits)}")
        self.assertEqual(report, [], "real names found; use neutral examples (laptop, workstation, cloud-vm, my-app)")


if __name__ == "__main__":
    unittest.main()

# Encrypted memory (optional git-crypt mode)

> Optional capability, **off by default**. Nestwork stores agent memory as plaintext
> Markdown in git. Turn this on only when memory accumulates content you do not want
> the git host — or anyone who obtains a clone — to read.

---

## 0. One-line definition

Transparent encryption for the few memory files that hold private content: the agent
reads and writes plaintext as usual, commits are encrypted automatically, and what
lands on the git host is ciphertext — while the rest of the repo (and any instance with
this mode off) stays plaintext.

## 1. Why this exists

Nestwork pushes memory to a git host (GitHub, etc.). Over time memory can accumulate
personal or otherwise private content you would rather the host — or anyone with a
clone — could not read. This is a **confidentiality** need, distinct from "fear of loss
or account ban" (that is a redundancy/backup concern, addressed by mirrors, not
encryption). The right fix for confidentiality is to make the content unreadable
(encrypt), not to move it to a different store.

Encryption carries real cost and a single point of failure (§4–§6), so for instances
with no privacy concern it is pure overhead. Hence opt-in:

- **Default OFF** — no git-crypt rules in `.gitattributes`, no tooling required, memory
  stored as plaintext.
- **Opt-in ON** — when you judge there is genuinely private content, follow §3 and
  encrypt only that small set of files.

## 2. When it applies

**Applies** when memory genuinely contains private / non-shareable content that must be
*both* synced across machines *and* kept confidential.

**Does not apply** when:

- Memory has no privacy concern → stay OFF; do not add a key single-point for nothing.
- The private content does not need multi-machine sync → simplest fix is to **not commit
  it at all** (a local, unsynced directory); no git-crypt needed.
- What you fear is loss / account ban, not reading → that is backup redundancy;
  encryption is the wrong tool.

## 3. Enabling (tested, single-key setup)

Prereq: repo is a git repo with a remote. Run from the repo root.

```bash
# 0. Full backup first (rollback path)
git bundle create ~/repo-pre-crypt.bundle --all
cp -a . ~/repo-dir-backup

# 1. Install git-crypt
apt-get install -y git-crypt    # macOS: brew install git-crypt | Windows: scoop/choco install git-crypt

# 2. Init with the DEFAULT key (do NOT use -k <name>, see pitfall #1)
git-crypt init

# 3. Export the key OUTSIDE the repo; never commit it
git-crypt export-key ~/myrepo-gitcrypt.key

# 4. Declare which paths are encrypted (.gitattributes itself stays plaintext — git must read it)
printf 'shared/memory.md filter=git-crypt diff=git-crypt\nagents/**/memory.md filter=git-crypt diff=git-crypt\n' > .gitattributes

# 5. Re-add to trigger encryption, then commit
git add .gitattributes shared/memory.md $(find agents -name memory.md)
git commit -m "security: encrypt memory files with git-crypt"

# 6. Verify ciphertext (must use cat-file, NOT git show — see pitfall #2)
git cat-file -p HEAD:shared/memory.md | head -c 12 | od -c   # expect \0 G I T C R Y P T \0
```

### Optional: purge plaintext already in history

`git-crypt init` only encrypts the *future*; plaintext already committed remains on the
host. To remove it you must rewrite history:

```bash
apt-get install -y git-filter-repo
git-filter-repo --force --invert-paths --path shared/memory.md --path-glob 'agents/*/*/memory.md'
git remote add origin <url>                      # filter-repo drops the remote
git push --force origin main
git branch --set-upstream-to=origin/main main    # see pitfall #3
```

Then redo §3 from step 2. Cost: **every clone diverges** — each machine needs
`git fetch && git reset --hard origin/main && git-crypt unlock <key>`.

### Each new machine: one command

```bash
git-crypt unlock /path/to/myrepo-gitcrypt.key    # run once after clone, then transparent
```

## 4. Key discipline (the durable asset)

1. **One encrypted repo = one key, copied to every machine.** Machine count does not
   multiply key complexity; only the number of encrypted repos does.
2. **The key never enters the repo** — not on the host, not in any mirror/backup.
3. **Back the key up offline in ≥2 places** (password-manager attachment + offline
   media). Lose every copy and all ciphertext is permanently unreadable — anything
   restored from backup is also unreadable ciphertext (a fake backup).
4. **Never transmit the key over a plaintext channel** (chat/email). A password-manager
   attachment doubles as the transport.
5. **Minimize encryption scope** — encrypt only files that truly hold private content
   (typically memory); keep portable methodology docs plaintext so they stay reusable.

## 5. Three real pitfalls (a paper plan will get these wrong)

- **#1 · Named-key mismatch.** `git-crypt init -k <name>` configures filter
  `git-crypt-<name>`, which does **not** match `filter=git-crypt` in `.gitattributes` →
  **silent no-op encryption** (looks successful, blobs stay plaintext). For a single-key
  setup you **must** use the bare `git-crypt init` (default key).
- **#2 · `git show` lies about ciphertext.** When unlocked, `git show` / `git diff` pass
  through the diff filter and **display plaintext**; verifying with them makes you think
  encryption failed (or succeeded when it didn't). Verify ciphertext **only with
  `git cat-file -p <blob>`** (raw blob, unfiltered).
- **#3 · filter-repo loses upstream.** `git-filter-repo` removes the remote; after
  re-adding it the branch **loses upstream tracking** → the Nestwork pre-write hook's
  `git pull --rebase` reports `no upstream` → **all memory writes are blocked**. Fix:
  `git branch --set-upstream-to=origin/main main` (only the machine that rewrote history
  needs this; fresh clones don't).

## 6. Anti-patterns

- **Encrypting every instance by default.** Most instances have no privacy concern and
  gain only a key single-point. The feature exists precisely as opt-in.
- **Expecting encryption to hide content from the agent's model provider.** The agent
  auto-decrypts → plaintext enters the API request. Encryption blocks *random exposure
  via the git host or anyone who obtains a clone*; it **accepts** that whoever runs the
  agent processes plaintext. Make the trust boundary explicit.
- **Leaking via filenames / commit messages.** Filenames, directory names, commit
  messages, and file sizes are all plaintext. For truly high-sensitivity cases use
  meaningless filenames + a uniform commit message (or pack the whole directory into a
  single encrypted blob).
- **Key and ciphertext on the same device with no passphrase.** A stolen device has both
  → directly decryptable (protects against the host, not against device loss). For
  extreme cases add a passphrase on top of the key.

## 7. Integration with other parts of Nestwork

- **Pre-write hook** (see `AGENTS.md` write protocol): encryption is transparent to the
  hook — the clean filter is deterministic (same plaintext → same ciphertext, no
  spurious diffs); the only catch is pitfall #3's upstream tracking after a history
  rewrite.
- **Desensitization** ([docs/desensitization-prompt.md](desensitization-prompt.md)):
  orthogonal. Desensitization rewrites content to be *safe to store*; encryption makes
  content *unreadable to the host*. Use desensitization for content you may later
  publish; use encryption for content that must stay private but synced.
- **Backup redundancy** (mirrors): a separate concern. Encryption covers confidentiality
  only, never availability — keep your mirror/backup story independent.

## 8. Maintenance

- This describes an **optional** capability of the Nestwork protocol; the methodology is
  upstream, but **no key and no private content ever appear here**.
- Last reviewed: 2026-06-06.
- Known stale conditions: git-crypt CLI flag changes; a future built-in encryption mode
  in the install scripts would supersede these manual steps.

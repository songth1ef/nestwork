---
title: Encrypt AI Agent Memory in Git with git-crypt
description: Encrypt AI agent memory with git-crypt: the agent reads plaintext, the git host stores ciphertext. Tested steps, topic-memory rules and limits.
keywords: encrypt AI agent memory, git-crypt memory, private AI memory, git-crypt tutorial, nestwork, agent memory privacy
date: 2026-09-27
---

**How do you keep an AI agent's memory private when it lives in a git repo on GitHub?** Use git-crypt on just the memory files. The agent keeps reading and writing plaintext on your machines, git encrypts the files as they are committed, and what the git host stores is ciphertext. nestwork documents this as an optional, off-by-default mode, with steps tested on git-crypt 0.8.0.

Encryption has limits worth knowing before you start: commit messages and file names stay readable, one lost key means lost memory, plaintext already pushed stays in history until you rewrite it, and the model provider still sees the plaintext. This article covers all of that.

## Do you need it at all?

nestwork stores memory as Markdown in a private repo. For most people that is enough. The [encrypted memory guide](https://github.com/songth1ef/nestwork/blob/main/docs/encrypted-memory.md) is blunt about when encryption is the wrong tool:

| Your worry | Right answer |
|---|---|
| Memory holds private content that must sync across machines *and* stay unreadable to the git host | git-crypt, on a small set of files |
| Private content that does not need to sync | Don't commit it at all; keep it in a local, unsynced directory |
| Losing the repo or the account | Backups and mirrors; encryption does nothing for availability |
| No real privacy concern | Stay off; a key is a new single point of failure |

The author of nestwork describes using it this way: the repo is private and self-owned, and "for the deeper secrets, I layered on git-crypt on top", so what lands on GitHub is ciphertext ([16 agents, one brain](../16-agents-one-brain/)).

## Step by step: enable git-crypt on a nest

Run these from the repo root. The first step is a backup, because the later steps can go wrong in quiet ways.

```bash
# 0. Full backup (your rollback path)
git bundle create ~/repo-pre-crypt.bundle --all
cp -a . ~/repo-dir-backup

# 1. Install git-crypt
brew install git-crypt          # Debian/Ubuntu: apt-get install -y git-crypt

# 2. Init with the DEFAULT key (no -k <name>)
git-crypt init

# 3. Export the key OUTSIDE the repo; never commit it
git-crypt export-key ~/myrepo-gitcrypt.key

# 4. Declare what gets encrypted (single-file memory)
printf 'shared/memory.md filter=git-crypt diff=git-crypt\nagents/**/memory.md filter=git-crypt diff=git-crypt\n' > .gitattributes

# 5. Re-add so the filter runs, then commit
git add .gitattributes shared/memory.md $(find agents -name memory.md)
git commit -m "security: encrypt memory files with git-crypt"

# 6. Verify the stored blob is ciphertext
git cat-file -p HEAD:shared/memory.md | head -c 12 | od -c   # expect \0 G I T C R Y P T \0
```

`.gitattributes` itself stays plaintext, since git has to read it. The git-crypt project also warns to put these rules in place *before* adding sensitive files ([git-crypt README](https://github.com/AGWA/git-crypt)).

On every other machine, after cloning, run once:

```bash
git-crypt unlock /path/to/myrepo-gitcrypt.key
```

From then on it is transparent: nestwork's hooks pull, commit and push as usual, and the clean filter is deterministic, so unchanged files do not produce spurious diffs.

## Topic memory: encrypt the whole scope, not just the index

The patterns above assume one `memory.md` per scope. Under protocol 3.1, a scope can switch to topic memory, where `memory.md` is only a generated index and the facts live in files like `shared/<topic>.md`. Those files would stay plaintext. Cover the directories instead:

```gitattributes
shared/** filter=git-crypt diff=git-crypt
agents/** filter=git-crypt diff=git-crypt
```

`**` matches every depth, so topic subfolders and each agent's mailbox `outbox/` are covered too. This was checked with git-crypt 0.8.0: every file under both directories was stored as `GITCRYPT` ciphertext, and files outside them stayed plaintext. Re-run the step 6 check on one topic file.

Two practical consequences:

- `scripts/maintenance/memory-index.py` and `distill.py` read the working tree, so run them only on an unlocked clone. On a locked clone they see ciphertext.
- With `agents/**` encrypted, each agent's `resident.md`, which loads at session start, is encrypted as well. Every machine that runs an agent has to be unlocked, or the agent starts with unreadable context.

## Three pitfalls the docs call out

1. **Named keys silently do nothing.** `git-crypt init -k <name>` configures a filter called `git-crypt-<name>`, which does not match `filter=git-crypt`. Everything looks fine and the blobs stay plaintext. For a single key, use bare `git-crypt init`.
2. **`git show` lies.** On an unlocked clone, `git show` and `git diff` pass through the filter and display plaintext. Verify only with `git cat-file -p`, which shows the raw blob.
3. **History rewrites break upstream tracking.** After a history rewrite (next section) the branch loses its upstream, nestwork's pre-write `git pull --rebase` fails, and every memory write is blocked. Fix it with `git branch --set-upstream-to=origin/main main` on the machine that did the rewrite.

## Already pushed plaintext? You have to rewrite history

`git-crypt init` protects future commits only. Anything committed before is still readable in history on the host. Removing it means rewriting history, for example with [git-filter-repo](https://github.com/newren/git-filter-repo):

```bash
git-filter-repo --force --invert-paths --path shared/memory.md --path-glob 'agents/*/*/memory.md'
git remote add origin <url>                      # filter-repo drops the remote
git push --force origin main
git branch --set-upstream-to=origin/main main
```

Adjust the paths to match what you encrypt; with topic memory, memory lives in more files than `memory.md`. Since the removed paths are rewritten out of the current commit too, check your working tree and restore the files from the step 0 directory backup if needed. Then redo the setup from step 2.

The cost is real: every other clone now has diverged history and needs `git fetch && git reset --hard origin/main && git-crypt unlock <key>`.

## What encryption does not hide

- **Commit messages.** git-crypt does not encrypt file names, commit messages or other metadata, and does not hide file sizes or when files change ([git-crypt README](https://github.com/AGWA/git-crypt)). nestwork's own commits are formulaic, such as `memory: update <host>/<agent-id>` or `comms: task to <host>/<agent-id> (<id>)`, so they reveal machine names, agent ids and activity timing, but not content. Anything you type into a manual commit message is public to the host.
- **File names.** A topic file called `health.md` announces its subject, and topic descriptions copied into an unencrypted index are readable too. For high-sensitivity cases the guide suggests meaningless file names and a uniform commit message.
- **The model provider.** The agent decrypts to read, so plaintext enters the API request. Encryption protects against the git host and anyone who obtains a clone, not against whoever runs the agent.
- **A stolen laptop.** If the key and the unlocked clone sit on the same device with no passphrase, the thief has both.

## Key backups, and why keys never go into memory

Treat the exported key as the durable asset. The guide's rules: one key per encrypted repo, copied to every machine; the key never enters the repo or any mirror of it; at least two offline backups, such as a password-manager attachment plus offline media; never send it over chat or email. Lose every copy and the ciphertext is unreadable for good, including every backup of the repo.

git-crypt also cannot revoke access: its README notes that anyone who once had the key can still read older history even after rotation.

Encrypted or not, API keys, tokens and passwords do not belong in agent memory. nestwork's README says so directly: a private repo can still leak through a host vulnerability, a compromised account or a wrong collaborator permission, and the agent loads memory into model requests as plaintext anyway. Keep secrets in environment variables or a secret store, and let memory say only *where* a credential comes from.

## FAQ

### Does git-crypt slow nestwork down?

The guide notes that encryption is transparent to the hooks and the clean filter is deterministic. It does not publish timing numbers, so none are claimed here.

### Can I encrypt only one agent's memory?

Yes. The patterns are ordinary `.gitattributes` rules, so you can target one scope, such as a single agent directory. The guide recommends keeping the encrypted scope as small as possible.

### Does `update.sh` still work on an encrypted nest?

Yes, with the current updater. It extracts upstream files without running your smudge filter and stages them through your clean filter. Commit or stash local changes first, then check that `VERSION` is not empty and that encrypted files remain encrypted.

### Is this built into the installers?

No. It is a manual, opt-in procedure. The protocol deliberately does not bake encryption in.

## Related

- [Git-native memory for AI agents](../git-native-agent-memory/)
- [Agent-to-agent communication with a git mailbox](../agent-mailbox-git/)
- [nestwork setup FAQ](../nestwork-getting-started-faq/)
- [What AI agent long-term memory is like in practice](../long-term-memory-in-practice/)
- [Your AI agent forgets everything when you switch devices](../agent-amnesia-cross-device/)

# nestwork: one shared brain for all your AI agents, across machines and vendors

> Current behavior aligned with protocol 3.0: resident startup; history and inbox on demand. [Loading and migration](../context-loading.md).

> Title candidates:
> - nestwork: one shared brain for all your AI agents
> - One git repo that holds the memory of every machine and every agent you run
> - Not another memory database, a protocol for multi-agent collaboration

![nestwork: many agents sharing one brain across devices and vendors](images/nestwork-overview-cover-nw.png)

You have probably lived through this. You brief a project to Claude Code on your laptop, then you switch to your desktop, open Codex, and it knows nothing. So you re-explain the conventions, the background, the traps you already hit.

And that is before you account for tools changing constantly. Almost every month there is a new "current best" model. You went from Cursor to Claude Code, then tried Codex, then Gemini. Sometimes the switch is not even your call: policy, region, account, price, and one day the tool you depend on just stops working for you. Every switch drops your agent back to "nice to meet you."

nestwork exists for exactly this. In one sentence: it turns the memory of all your agents into plain text inside a git repo you own, so they share one brain across machines, across tools, and across vendors.

It is not a tool, not a hosted service, and it needs no server. It is a protocol. Here is everything it does, laid out in one pass.

![nestwork architecture: the git repo layer, sync layer, multi-agent access layer, and protocol governance layer](images/nestwork-overview-architecture-nw.png)

## 1. Memory is just markdown in git

The foundation of nestwork is almost counterintuitively simple: all memory is plain markdown files in a git repo, and that repo is the single source of truth. An agent pulls before it works, then commits and pushes when it is done. No database, no backend, no account to sign up for.

Because memory is plain text, you can open it, edit it, or roll it back at any time with any editor or any git tool. It reads for humans and it reads for agents. How a piece of memory came to be, and when it changed, is right there in the git log.

## 2. One shared memory, across machines and vendors

Since sync rides on a git remote, the agents on your laptop, your desktop, a few Linux boxes, even an Android phone, all live in the same brain as long as they can push. They do not need to sit on the same machine, and nobody has to open a port for anyone.

What it is compatible with is a whole class of agents: Claude Code, Codex CLI, Gemini CLI, Hermes, OpenClaw, and other markdown-configured tools. The same memory reads fine no matter who shows up.

This is exactly what catches the moving-tools problem. Binding your memory to one tool is a bet that the tool never gets retired and never becomes unusable. Plain text bound to git is not picky about tools: the day you want to move wholesale from an overseas tool to a domestic model, the context stays put, and the only thing you swap is the agent reading it.

## 3. Inherit it in one click, and the memory lives in your own repo

Onboarding is git's native tongue. Click Use this template on GitHub and you inherit the whole protocol skeleton; clone it and you are connected.

There is an underrated point here: what you inherit is a private repo of your own. From day one the memory lives in your hands, not parked in some vendor's backend. With a hosted memory service, you hand the context over and it sits in someone else's store; with nestwork, ownership of the data never leaves you.

Inheriting instead of forking has another upside. When upstream updates the protocol, it goes through its own update flow that touches the protocol layer and cannot touch your private memory. The strategy you built up over months, and each agent's memory, will not get wiped by a single upstream sync.

## 4. Private, and encryptable, so you dare to write the real stuff

Putting memory in a private repo is only the first layer. For genuine secrets, you can stack git-crypt on top and encrypt before anything enters the repo. Even if the repo is hosted on GitHub, what lands there is ciphertext; the plaintext is unreadable. The data is yours, and so is the key.

For anyone who wants to feed an agent project internals, internal war stories, or business judgment, this is not a nice-to-have. It is the precondition for daring to use it at all.

## 5. The hard part is "how do a pile of agents not fight"

If this were only "use git to store markdown," it would be a clever little trick. What nestwork actually thought through is the dirty work of many agents on many machines working at the same time.

Write isolation. Every machine and every agent owns, and only writes, its own directory, with a path that looks like this: agents/<host>/<agent-id>/. Nobody writes into the same file as anyone else, so conflicts have nowhere to start. And if a collision does happen, the conflict resolution rules are hardcoded: take local for your own directory, take remote for someone else's directory, take remote for the upstream-managed shared layers. Whoever owns it decides.

Atomic sync. Pull --rebase before every write, commit and push after, with automatic retry on failure. This runs on its own once the hooks are installed, which squeezes the race window down to the single instant of one write, instead of leaving the whole session wide open.

Layered priority and resolution. Memory is ranked: behavior rules > strategy > shared memory > each agent's private memory > projects > methodology. When two instructions conflict, the higher-priority one wins, and you do not blend the two together. It is this chain that keeps a dozen-plus agents behaving consistently, all reading the same "constitution."

Distillation. How do the scattered private observations of each agent settle into facts the whole fleet shares? Through a distillation flow: first a sub-agent reviews for sensitive data, contradictions, and stale entries, then a human confirms, and finally it is merged into shared memory non-destructively, merge and add only, never deleting the original records.

Agents can leave each other notes. There is a built-in git-native mailbox. An agent on machine A finishes a stretch and leaves a line for the agent on machine B: "I'm done with this part, you take it from here," and B reads the unread note on demand when coordinating the relevant task. No message queue, no service, just write a file into the repo and push it up.

![multiple agents each tending their own square, collaborating in order and leaving each other notes through the mailbox](images/nestwork-overview-coordination-nw.png)

## 6. It is a protocol, so it governs more

Calling it a protocol is not just rhetoric. Beyond storing and syncing, it also lays down a full set of rules for "how to use memory."

Resident startup, on-demand history. In protocol 3.0, the hook pulls and emits paths for core rules and optional shared/agent resident summaries. Strategy, historical memory, projects, methodology and inbox contents are retrieved only when the task needs them. Missing summaries never cause full-history fallback.

There are explicit rules for where memory goes. Project conventions and lessons go into the project's own docs, cross-project reusable methodology goes into workflow, the current project's business and decisions go into projects, cross-device protocol goes into the agent's private memory, and stable cross-agent facts go into shared memory. Knowledge has a fixed home, so it does not turn into a mess.

Oversized files split automatically. Any markdown that goes past its line limit gets split by topic into an "index plus sub-files," keeping each file focused so agents retrieve more accurately.

Version governance. The protocol marks its evolution with MAJOR.MINOR, a private instance can pin a version it trusts, and it can also override the default line limit with a local file. It behaves like a spec that iterates, not a static piece of software.

## 7. And there is more (optional, turn it on when you need it)

- If you use claude-mem, nestwork will export its observations at the end of a session and push them along with your memory, giving its notes cross-machine reach too.
- High-frequency, bulky artifacts like local history are stored on a separate orphan branch per agent, keeping the main branch lean so it does not balloon over time.
- When you absorb content from an external working directory into nestwork, there is a contract with desensitization rules, so secrets do not get hauled in naked.

## Getting started

Head to GitHub: songth1ef/nestwork. If you find it useful, give it a star first.

```bash
# 1. Click Use this template on GitHub to create your own private repo
# 2. Clone it down
# 3. Install hooks for each tool
bash scripts/install/claude.sh
bash scripts/install/codex.sh
bash scripts/install/gemini.sh
```

Once that is done, pull / commit / push all run automatically. You use your agents as usual, except this time, switch machines, switch tools, switch models, and they still remember.

Try it for a week on two devices and two tools. The day you change machines, or move from one tool to another, and you open an agent and it picks up yesterday's work mid-sentence, you will get why this matters.

<!-- nestwork overview | EN -->

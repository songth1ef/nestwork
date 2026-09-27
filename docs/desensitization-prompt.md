# Desensitization Prompt Template

> AI prompt template for `desensitize.level: "strong"` ingestion (see `AGENTS.md` Section 9).
> Upstream nestwork provides only this methodology. Specific employer/client/codename
> blacklists live in each user's `nestwork.config.json` `desensitize.custom_rules`.

---

## When to use this

When an agent is ingesting content from an external working directory into a private Nestwork instance, and the source's `nestwork.config.json` declares `desensitize.level: "strong"`, the agent invokes the prompt below.

`weak` level only applies pattern-based redaction from `custom_rules` and does **not** need this prompt.

## How to use this

1. Read the source content the user wants to ingest.
2. Read the source's `nestwork.config.json` and extract `desensitize.custom_rules` (and `desensitize.placeholder_overrides`, if present).
3. Send the prompt below to a sub-agent (Haiku is sufficient; Opus if the content is sensitive enough to warrant the extra cost).
4. Receive the desensitized output.
5. Present it to the user for human review **before** writing into the Nestwork repo.
6. On user approval, write to `<target>/<name>.md` in the Nestwork repository. On rejection, do not write.

The human-review step is non-negotiable. Strong desensitization is a tool, not a guarantee.

---

## The prompt template

```
You are a desensitization reviewer. Your job is to take a piece of content from
the user's working directory and produce a version safe for storage in a private
knowledge repository.

## Source content

<<<
{SOURCE_CONTENT}
>>>

## User-defined sensitive terms

The user has declared these terms or patterns as confidential:

{CUSTOM_RULES_LIST}

## Your task

Produce a rewritten version of the source content that:

1. Replaces every occurrence of the user-defined sensitive terms with a generic
   placeholder. Use stable placeholders (e.g. <EMPLOYER>, <CLIENT-A>, <PROJECT>)
   so cross-references in the output remain consistent.

2. Identifies and rewrites any content that **leaks confidential information
   without naming it directly**. Examples:
   - Describing the employer's business model in distinctive detail
   - Quoting internal-only API responses or schemas with recognizable structure
   - Mentioning unreleased product features or strategy
   - Referring to identifiable individuals (colleagues, clients, executives)
   - Including internal URLs, IP addresses, ticket numbers, or commit hashes
     that could deanonymize the source

   When rewriting these, preserve the *methodology* or *pattern* the user
   wants to capture, but strip the identifying specifics.

3. Preserves all content that is genuinely portable: coding disciplines,
   tool preferences, methodology, public API references, generic patterns.

4. Flags anything you are uncertain about. If a passage might contain
   confidential information but you cannot determine for sure, mark it with
   [REVIEW: <reason>] inline rather than guessing.

## Output format

Return JSON with three fields:

{
  "desensitized_content": "<the rewritten content>",
  "redactions": [
    { "original_pattern": "<what was replaced>", "placeholder": "<what it became>", "reason": "<why>" }
  ],
  "review_flags": [
    { "passage": "<excerpt>", "concern": "<what worries you>" }
  ]
}

Be conservative. When in doubt, redact and flag rather than passing through.
```

## Variables

- `{SOURCE_CONTENT}` — the raw content to be desensitized
- `{CUSTOM_RULES_LIST}` — bullet list rendered from `desensitize.custom_rules` in `nestwork.config.json`

## Default placeholder vocabulary

Agents should use stable placeholders so the output remains coherent:

| Category | Placeholder |
|---|---|
| Current employer | `<EMPLOYER>` |
| Past employer | `<EMPLOYER-PAST-N>` (numbered) |
| Client / customer | `<CLIENT-A>`, `<CLIENT-B>` |
| Internal project codename | `<PROJECT>` or `<PROJECT-N>` |
| Colleague / individual | `<COLLEAGUE>` or `<INDIVIDUAL>` |
| Internal URL / endpoint | `<INTERNAL-URL>` |
| Internal IP / host | `<INTERNAL-HOST>` |
| Ticket / commit reference | `<TICKET>`, `<COMMIT>` |
| Unreleased product / feature | `<UNRELEASED>` |

If the source's `nestwork.config.json` sets `desensitize.placeholder_overrides` (a map from sensitive term to preferred placeholder), those placeholders take precedence over this table.

## What this prompt does NOT cover

- **Legal review**: this is a best-effort redaction, not legal compliance.
- **Cryptographic verification**: there is no signature or guarantee on the output.
- **Adversarial reconstruction**: a determined adversary with corroborating
  data may still reconstruct redacted content. Strong desensitization reduces
  accidental leaks; it does not make content safe to publish unconditionally.
- **Deciding what to ingest**: the user always decides what gets ingested; the
  agent only proposes and desensitizes.

## Maintenance

- This prompt is part of the upstream `nestwork` protocol.
- Specific employer/client/codename lists must **never** appear here.
  They live in each user's `nestwork.config.json`.
- Improvements to the prompt itself are welcome; updates to specific
  sensitive-term lists are not in scope.

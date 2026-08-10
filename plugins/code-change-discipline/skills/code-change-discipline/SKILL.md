---
name: code-change-discipline
description: "How to find, read, edit and verify code in an existing repository without burning context or guessing. Invoke it BEFORE the first search and BEFORE the first edit of any code task, at any size — a one-line fix and a thousand-site migration use the same ladder. Triggers on: fix this bug, why is this failing, debug this, refactor X, rename X, extract this, add a field, add a parameter, add an endpoint, change how X works, wire up X, update the handler, remove this code, delete dead code, where is X handled, find every place that X, which files do I need to touch, is this still used, make this change, apply this fix. Covers the codebase-memory-mcp discovery ladder and its silent truncation signals, when to fall back to LSP and when to fall back to grep, the narrow-window Read-then-Edit protocol, and verification by test count. Not for prose or docs-only edits, config-file tweaks, brand-new standalone scripts, or conversation that touches no repository."
---

# Code change discipline

Applies to **every** code change in an existing repo. Size decides whether you fan out to subagents
(see `sweeping-change`); it never decides whether you verify.

## 0. Orient before you search — once per repo

`list_projects` → find the repo by its **`root_path`**, not by guessing the name. The names are
inconsistent (`api-server` vs `Users-me-src-acme-api-server`). Copy the `name` string
verbatim. **`project` is required on every codebase-memory-mcp tool except `list_projects`.**

`index_status(project=…)` → compare `head_sha` with `base_sha`. Different means the index predates
commits on disk. There is no dirty flag; `detect_changes(project=…)` shows working-tree drift.
When they differ, **confirm anything load-bearing with LSP or a narrow Read before you edit.**

Nothing in `list_projects` matches → §3.

## 1. The discovery ladder

**Do not use Grep or Glob to find code, and never Read a large file in order to search it.**
Grep here returns hundreds of unranked hits and will exhaust your context before you finish.
Use, in this order:

1. `search_code(project=…, pattern=…, mode="files")` to scope, then re-call with
   `mode="compact", context=N` — graph-augmented grep that returns the CONTAINING SYMBOL, which
   plain grep cannot. `path_filter` is a regex over result paths; `file_pattern` is a glob handed
   to `grep --include`. Use `mode="full"` only when you actually need the source text.
2. `search_graph(project=…, query=…)` for BM25 discovery, `name_pattern=…` for exact regex.
   **They are not additive — when `query` is set, `name_pattern` is ignored.** `semantic_query`
   takes an **array** of keywords (`["payoff","quote"]`), never a bare string, and its hits come
   back under `semantic_results`, not `results`.
3. `get_code_snippet(project=…, qualified_name=…)` — reads exactly one symbol. Prefer over Read.
4. LSP — §2.

**Detect truncation every time; it is silent.**

- `search_code`: compare `total_grep_matches` (raw hits) and `total_results` (deduped functions)
  against your `limit` (default **10**). There is **no `offset` and no `has_more`** — to see more,
  raise `limit` or narrow with `file_pattern` / `path_filter`.
- `search_graph`: `limit` defaults to **200**; page with `total` + `has_more` + `offset += limit`.
- **A count taken from a truncated response is not a count.** State the number and how you got it.

## 2. LSP is the tiebreaker — trust it over the graph

Use LSP **whenever the graph output looks wrong, stale, ambiguous or incomplete**, and always before
an edit whose correctness depends on who calls what. The graph resolves calls by name and can
collapse same-named methods from different interfaces into one node; **verify whenever a name is
shared.**

Every operation requires `filePath`, `line` and `character` — **including `workspaceSymbol` and
`documentSymbol`**; anchor those two at any real file in the repo (line 1, character 1 is fine).
Line and character are **1-based**, as shown in the editor.

- `workspaceSymbol(query=…)` — entry point when you have a name and no file. It needs a real
  `query`; most servers return nothing for an empty one.
- `documentSymbol` — a file's structure without reading its text.
- `goToDefinition`, `hover` — resolve the symbol under a position.
- `findReferences` — the reliable way to count call sites.
- `goToImplementation` — interface implementors.
- `prepareCallHierarchy` **first**, then `incomingCalls` / `outgoingCalls` at the same position.
  Skipping the prepare step is why call hierarchy comes back empty.

## 3. When the ladder is short, degrade out loud

Name the rung you are on before you rely on a count.

**Repo not indexed.**

1. Check for an indexed parent or sibling — monorepo subrepos are indexed separately.
2. Offer `index_repository` and let the user decide; it writes, and it takes minutes.
3. Until then run **LSP-first**: `workspaceSymbol` to find, `documentSymbol` to survey a file,
   `findReferences` to count.
4. Grep last, and disciplined: file list first (`--files-with-matches`), then one narrow pattern
   with line numbers. Never Read a file over ~500 lines to search it.

**No language server for the language.** Know which servers you actually have before you plan around
LSP — most setups cover one or two languages, not all of them, and some servers have startup
requirements that silently produce empty results (see the plugin README). **One probe, then stop: if
LSP reports no server for a language, do not retry it symbol by symbol.** The graph and `search_code`
become authoritative, and any count must come from a **script or regex reused verbatim**, not from
eyeballing a result list.

**Neither.** Say so in one line, grep as in step 4, and treat every number as a lower bound.

## 4. Editing protocol

Locate the site with `search_code` or LSP (both give file:line), then
`Read(file_path, offset=…, limit=…)` a NARROW window, then Edit with a tight `old_string`.
Line numbers from a plan, an earlier session, or the index are **NOT durable — re-derive them.**
Never edit from a graph snippet without confirming the current text on disk; the index can be
commits behind.

## 5. Verify by number, not by colour

- Know the test count **before** you start. Track it as a **number that must be accounted for**,
  not merely "green". An unexplained delta is a finding, in either direction.
- Run the build and the suite yourself. A report that it passed is not evidence.
- **Harness diagnostics captured mid-edit look exactly like real failures.** Errors reported while
  a file is being refactored are frequently stale. Confirm against a real build before acting.
- **Tests can pin a bug as correct.** More than once, an assertion has documented broken behaviour
  as expected. A passing suite is not evidence that behaviour is right.
- **You will be wrong too.** When you find you stated something false, correct the record plainly.

## 6. If the work outlives one context, write the corrections down

A second session, a subagent, or a compaction loses everything you learned that is not on disk.
The moment the job needs any of those, keep a document with an **execution log near the top** that
**overrides the plan body where they disagree** — corrected counts, plan claims found false, and
decisions later work must follow. `sweeping-change` has the full machinery; use it as soon as the
work stops fitting in one pass.

## Anti-patterns

- Grepping first "just to have a look".
- Quoting a count off a response whose `total_results` exceeded `limit`.
- `search_graph(direction=…)` — no such parameter; use `trace_path` for direction.
- Retrying LSP after it has already reported no server for that language.
- Reading a whole file to change three lines of it.
- Calling any codebase-memory-mcp tool without `project=`.

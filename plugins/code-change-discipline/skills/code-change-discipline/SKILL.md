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

Indexes auto-refresh, so there is no stale-SHA check to run. Freshness is a **per-path** question:
`index_status(project=…, diagnostics="summary")` for readiness and coverage gaps, then
**`check_index_coverage(project=…, paths=[…])` on every path you are about to cite.** A clean
result means no *recorded* gap — not proof of completeness. Where coverage comes back partial,
skipped, excluded, stale or unknown, read the reported range directly before relying on it.

Nothing in `list_projects` matches → §3.

## 1. The discovery ladder

**Do not use Grep or Glob to find code, and never Read a large file in order to search it.**
Grep here returns hundreds of unranked hits and will exhaust your context before you finish.

The tool reference — the decision matrix, edge types, Cypher, evidence tiers — is the
**`codebase-memory` skill that codebase-memory-mcp ships and keeps in step with its own releases.**
Use it for *what to call*. This section covers only what that reference leaves out, plus the places
it is wrong.

Order: `search_code` to scope → `search_graph` to find symbols → `get_code_snippet` to read one →
LSP (§2) to settle anything load-bearing.

**Defaults that silently narrow your results.** Each of these produces a confident wrong answer
rather than an error:

- **`search_code(regex=…)` defaults to `false`.** Patterns are literal. A regex typed without it
  matches nothing and looks like an honest zero.
- **`trace_path(include_tests=…)` defaults to `false`.** Every trace omits test call sites, so a
  call-site count taken from a default trace is not a count of call sites.
- **`get_code_snippet(source_mode=…)` defaults to `auto`, which OUTLINES any container over 200
  lines** instead of returning its source. Pass `source_mode="full"` when you need the text, and
  read `coverage_note` for the gaps.
- **`max_output_tokens`** exists on most tools and truncates to fit. Output can be cut for size
  alone, independently of any `limit`.

**Detect truncation every time; it is silent.**

- `search_code`: `limit` defaults to **10**. Compare `total_grep_matches` (raw hits) and
  `total_results` (deduped functions) against it, then page with `result_offset`/`result_limit`
  or narrow with `file_pattern` / `path_filter`.
- `search_graph`: `limit` defaults to **50**; page with `total` + `has_more` + `offset += limit`.
- `query_graph`: shows **200** rows by default (`max_rows`, up to 99998); page with `offset` or
  `cursor`, and put a `LIMIT` in the Cypher for broad queries.
- **A count taken from a truncated response is not a count.** State the number and how you got it.

**Corrections to the shipped reference.** It gets these wrong; the schema is authoritative:

- **`search_graph` has no `direction` parameter** — the reference suggests
  `search_graph(relationship="CALLS", direction=…)`. Degree there is undirected. To separate callers
  from callees, take the ranked names and run `trace_path(direction="inbound"|"outbound")`.
- `search_graph(query=…)` **ignores `name_pattern`** when both are given. `semantic_query` takes an
  **array** of keywords, never a bare string, and its hits come back under `semantic_results`.

**Tools the reference omits:** `get_file_outline` (one file's declarations without reading it —
prefer it to Read for orientation), `check_index_coverage` (§0), `compare_graphs` (two indexed
snapshots), and `query_graph(graph="missed")` for the coverage-gap file tree.

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

- **Get the test count without running anything.** Use the runner's discovery mode —
  `dotnet test --list-tests`, `pytest --collect-only -q`, `jest --listTests` / `vitest list`,
  `go test -list . ./...`, a Gradle/Maven dry run, or the IDE/LSP test explorer. Record it before
  editing and compare after. Track it as a **number that must be accounted for**, not merely
  "green". An unexplained delta is a finding, in either direction.
- **Do not run a pre-change baseline suite by default.** Run tests before editing only when you
  must tell a pre-existing failure from one you caused — the suite is known red or flaky, or the
  task is "why is this failing". Otherwise run the build and the tests **once, after** the change.
- **No red-green theater.** Never revert or stash finished work to show a new test failing, then
  reapply it. Write the test against the finished code and run it once. If you doubt it exercises
  the change, read the assertion — do not re-stage history.
- Run the build and the tests yourself after the change. A report that they passed is not evidence.
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
- Typing a regex into `search_code` without `regex=true`, then believing the zero.
- Counting call sites off a `trace_path` that still has `include_tests` defaulted to false.
- Treating an `auto` snippet of a large class as its source; it is an outline.
- Citing a path without `check_index_coverage`, or reading a clean coverage result as proof.
- `search_graph(direction=…)` — no such parameter; use `trace_path` for direction.
- Retrying LSP after it has already reported no server for that language.
- Reading a whole file to change three lines of it.
- Calling any codebase-memory-mcp tool without `project=`.

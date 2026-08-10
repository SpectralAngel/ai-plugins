# code-change-discipline

Discovery, editing and verification discipline for code changes in large repositories.

Install and requirements: see the [repo README](../../README.md). Short version — this plugin needs
[codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) and `ENABLE_LSP_TOOL=1` with
a language server for your stack.

## Skills

**`code-change-discipline`** — invoked before the first search and the first edit of *any* code
task, at any size. Owns:

- the discovery ladder: `search_code` → `search_graph` → `get_code_snippet` → LSP, with Grep and
  Glob explicitly off the table for finding code
- silent-truncation detection, which differs per tool (`search_code` has no `has_more` and defaults
  to `limit=10`; `search_graph` defaults to 200 and paginates)
- LSP as the tiebreaker over the graph, including the `prepareCallHierarchy`-first rule
- the narrow-window Read-then-Edit protocol, and why line numbers from a plan are not durable
- verification by test count rather than by "green"
- how to degrade out loud when the repo is not indexed or has no language server

**`sweeping-change`** — for work that outgrows one context. Owns only the delta: when to fan out to
subagents (roughly 50+ sites) and when not to, the reusable agent brief, worktree hygiene including
why worktrees must live outside syncing folders, and the execution log that overrides the plan body
where they disagree. Everything per-change still comes from `code-change-discipline`.

**`codebase-memory`** — the query reference. A decision matrix from question to tool call, the 14
MCP tools, edge types, Cypher examples for `query_graph`, and the pagination gotchas. Query
semantics live here; workflow lives in `code-change-discipline`.

## Hooks

`hooks/hooks.json` wires two scripts:

- **SessionStart** (`startup`, `resume`, `clear`, `compact`) → `session-code-discipline.sh` prints
  the reminder to stdout, which Claude Code prepends to the session context.
- **SubagentStart** (all subagents) → `subagent-code-discipline.sh` emits
  `hookSpecificOutput.additionalContext` as JSON.

Two things to preserve if you edit them:

- The SubagentStart payload **must stay on one line**. A raw newline makes the JSON invalid, and
  invalid JSON is dropped silently — the hook appears to run and does nothing.
- `session-code-discipline.sh` deliberately names no tool parameters. Signatures drift, and a
  half-accurate tool list in a reminder is what teaches a model to skim it. The skill is the source
  of truth; the hook only points at it.

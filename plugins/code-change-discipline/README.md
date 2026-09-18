# code-change-discipline

Discovery, editing and verification discipline for code changes in large repositories.

Install and requirements: see the [repo README](../../README.md). Short version — this plugin
augments [codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) **0.11.0 or later**
and expects `ENABLE_LSP_TOOL=1` with a language server for your stack.

## What this plugin does and does not own

codebase-memory-mcp installs its own `codebase-memory` skill, three read-only agents, search
augmentation hooks and session reminders. **That is the tool reference, and it ships in step with
the server.** This plugin deliberately does not fork it — an earlier version did, and every
duplicated parameter and default drifted out of date by 0.11.0.

What this plugin adds is everything the server says nothing about: when to invoke the discipline at
all, LSP as the tiebreaker, how to edit, how to verify, and how to run a change too large for one
context.

## Skills

**`code-change-discipline`** — invoked before the first search and the first edit of *any* code
task, at any size. Owns:

- orientation: matching the repo by `root_path`, and per-path freshness via `check_index_coverage`
  rather than a stale-SHA check (indexes auto-refresh now)
- the defaults that silently narrow results — `search_code(regex=false)`, `trace_path` excluding
  tests, `get_code_snippet` outlining containers over 200 lines, `max_output_tokens`
- silent-truncation detection, which differs per tool
- corrections to the shipped reference, including that `search_graph` has no `direction` parameter
- LSP as the tiebreaker over the graph, including the `prepareCallHierarchy`-first rule
- the narrow-window Read-then-Edit protocol, and why line numbers from a plan are not durable
- verification by test count rather than by "green"
- how to degrade out loud when the repo is not indexed or has no language server

**`sweeping-change`** — for work that outgrows one context. Owns only the delta: when to fan out to
subagents (roughly 50+ sites) and when not to, the reusable agent brief, worktree hygiene including
why worktrees must live outside syncing folders, and the execution log that overrides the plan body
where they disagree. Everything per-change still comes from `code-change-discipline`.

## Hooks

`hooks/hooks.json` wires three hooks, all as **inline commands with no script files**:

- **PreToolUse** on the read-only codebase-memory-mcp tools → emits `permissionDecision: "allow"`,
  so graph queries do not prompt in plan mode.
- **SessionStart** (`startup`, `resume`, `clear`, `compact`) → prints the reminder to stdout, which
  Claude Code prepends to the session context.
- **SubagentStart** (all subagents) → emits `hookSpecificOutput.additionalContext` as JSON.

Four things to preserve if you edit them:

- **The payloads must stay portable.** Shell-form hooks run under `sh` on macOS and Linux, and under
  Git Bash on Windows — or **PowerShell when Git Bash is absent**. `echo '...'` parses identically in
  both, which is why there are no `.sh` files here. Keep every payload inside single quotes, keep
  everything outside them to `echo` and `;`, use **no apostrophes** (unrepresentable inside an `sh`
  single-quoted string) and **ASCII only** (PowerShell mangles the rest). CI enforces all of this.
- **The allow-list lives in the PreToolUse `matcher`,** not in the command. The command is a
  constant, so the hook cannot leak an allow decision to a write tool. Adding a tool to the
  allow-list means editing that regex — and it is anchored with `$` on purpose.
- The SubagentStart payload **must stay on one line**. A raw newline makes the JSON invalid, and
  invalid JSON is dropped silently — the hook appears to run and does nothing.
- The reminders deliberately name **no tool parameters**. Signatures drift, and a half-accurate tool
  list in a reminder is what teaches a model to skim it. That rule is why this plugin's drift was
  confined to its skills. The skill is the source of truth; the hook only points at it.

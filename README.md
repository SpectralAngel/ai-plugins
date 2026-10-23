# ai-plugins

A Claude Code plugin marketplace. One plugin so far: **code-change-discipline**.

## code-change-discipline

An agent turned loose on a large repository will grep. Grep returns hundreds of unranked hits, the
agent reads a 3,000-line file to find three lines, and the context window is gone before any code
has been changed. This plugin replaces that with an explicit ladder — structural index first, a
language server as the tiebreaker, grep last and only when named out loud — plus the rules that keep
the rest of the change honest: detect silent truncation before quoting a count, read a narrow window
before editing, count tests from the runner's discovery mode instead of running a baseline.

It **augments** codebase-memory-mcp rather than wrapping it. That server ships its own skill, agents
and reminders covering which tool answers which question; this plugin covers what it leaves out.

Two skills and three hooks:

| Component | What it does |
|---|---|
| `code-change-discipline` (skill) | Orientation and per-path coverage checks, the defaults that silently narrow results, truncation detection, LSP as tiebreaker, the Read-then-Edit protocol, verification by test count. Fires before the first search and the first edit of any code task, at any size. |
| `sweeping-change` (skill) | What changes when the work outgrows one context: slicing across subagents, worktree hygiene, and the execution log that makes corrections compound instead of being rediscovered by every agent. |
| `PreToolUse` hook | Auto-approves the read-only codebase-memory-mcp tools, so graph queries do not prompt in plan mode. Write tools still prompt. |
| `SessionStart` hook | Injects the reminder to invoke the discipline skill at session start, resume, clear and compact. |
| `SubagentStart` hook | Same reminder into every subagent context, since a fresh subagent knows none of it. |

The hooks are the point. A skill that is never invoked does nothing, and "invoke this before you
search" is exactly the instruction a model skims past when it already has a plausible next action.

## Requirements

These are hard requirements, not suggestions — the skills build directly on these tools, and without
them most of the ladder has no rungs.

**1. [codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) 0.11.0 or later** — the
code knowledge graph. Install the binary from Releases, then let it configure itself:

```
codebase-memory-mcp install --clients=claude
```

That registers the MCP server, installs its `codebase-memory` skill, three read-only agents, and its
own search-augmentation and reminder hooks. This plugin assumes all of that is present and does not
duplicate it. Then, in a session, run `index_repository` on the repo root — it writes, and it takes
minutes. Re-index after upgrading the server.

Earlier releases will not do: this plugin's guidance names tools (`check_index_coverage`,
`get_file_outline`) and defaults (`search_code(regex=false)`) that only exist from 0.11.0.

**2. A language server, via Claude Code's LSP tool** — `"env": { "ENABLE_LSP_TOOL": "1" }` in
`settings.json`, plus a server for your stack (the `typescript-lsp`, `csharp-lsp` and `jdtls-lsp`
plugins in the official marketplace are the easy path). LSP is what the skills fall back to when the
graph looks stale or ambiguous, and `findReferences` is the only reliable way to count call sites.
codebase-memory-mcp has no LSP concept at all — this is the plugin's own contribution.

Without either one, the skills still tell you to degrade out loud and treat every count as a lower
bound — but you are getting a fraction of the value.

## Install

```
/plugin marketplace add SpectralAngel/ai-plugins
/plugin install code-change-discipline@ai-plugins
```

Restart the session so the hooks load.

## Permission prompts in plan mode

Read-only graph queries prompt for approval in plan mode, which makes the discovery ladder
unusable exactly where it matters most. A Claude Code plugin **cannot** ship permission rules —
`plugin.json` has no `permissions` field, and a plugin's `settings.json` supports only `agent` and
`subagentStatusLine` — so the fix here is a `PreToolUse` hook that returns
`permissionDecision: "allow"` for the thirteen read-only tools.

The allow-list is the hook's `matcher` regex, anchored with `$`. `index_repository`,
`delete_project`, `manage_adr` and `ingest_traces` are deliberately excluded and still prompt.

## Windows

The hooks are inline shell commands, not scripts, and every payload is single-quoted so it parses
identically under `sh`, Git Bash and PowerShell. **Git Bash is not required.** This matters because
Claude Code installs as a native binary, so neither Node nor Python is guaranteed to be present, and
a hook that cannot start fails *non-blockingly* — it looks like it ran and contributes nothing.

If you edit the hooks, keep the payload rules in
[the plugin README](plugins/code-change-discipline/README.md); CI enforces them.

## Turning the hooks off

The plugin injects text into every session and every subagent. If you want the skills but not the
nagging, disable the plugin and copy `plugins/code-change-discipline/skills/` into
`~/.claude/skills/` by hand, or fork and delete `hooks/hooks.json`. Note that this also gives up the
permission hook. There is no setting that keeps the skills and drops the hooks.

## Language servers — a gotcha worth knowing

`csharp-ls` searches its **working directory** recursively for solutions and never walks upward from
the file being edited. Given several it picks one arbitrarily and every request silently returns
"No symbols found". Start C# sessions in a directory with exactly one solution beneath it — never in
an umbrella folder containing several. `csharp-ls --diagnose --loglevel info` prints which one it
loads, without starting a session.

This is the class of failure the skills care about: not an error, just empty results that look like
an answer.

## Other agents

`AGENTS.md` in this repo states the same discipline without any Claude Code or MCP tool names, for
agents that read `AGENTS.md` rather than the Agent Skills format. The `SKILL.md` files are plain
Markdown with YAML frontmatter and are readable by any tool that supports the format.

## License

MIT. See [LICENSE](LICENSE).

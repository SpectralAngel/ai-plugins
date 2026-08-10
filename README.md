# ai-plugins

A Claude Code plugin marketplace. One plugin so far: **code-change-discipline**.

## code-change-discipline

An agent turned loose on a large repository will grep. Grep returns hundreds of unranked hits, the
agent reads a 3,000-line file to find three lines, and the context window is gone before any code
has been changed. This plugin replaces that with an explicit ladder — structural index first, a
language server as the tiebreaker, grep last and only when named out loud — plus the rules that keep
the rest of the change honest: detect silent truncation before quoting a count, read a narrow window
before editing, know the test count before you start.

Three skills and two hooks:

| Component | What it does |
|---|---|
| `code-change-discipline` (skill) | The ladder, LSP as tiebreaker, the Read-then-Edit protocol, verification by test count. Fires before the first search and the first edit of any code task, at any size. |
| `sweeping-change` (skill) | What changes when the work outgrows one context: slicing across subagents, worktree hygiene, and the execution log that makes corrections compound instead of being rediscovered by every agent. |
| `codebase-memory` (skill) | Query reference for the knowledge graph — which tool answers which structural question, edge types, Cypher examples, per-tool pagination gotchas. |
| `SessionStart` hook | Injects the reminder to invoke the discipline skill at session start, resume, clear and compact. |
| `SubagentStart` hook | Same reminder into every subagent's context, since a fresh subagent knows none of it. |

The hooks are the point. A skill that is never invoked does nothing, and "invoke this before you
search" is exactly the instruction a model skims past when it already has a plausible next action.

## Requirements

These are hard requirements, not suggestions — the skills name specific tools and their exact
parameters, and without them most of the ladder has no rungs.

**1. [codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp)** — the code knowledge
graph. Install the binary from Releases, register it, and index each repo you work in:

```jsonc
// ~/.claude.json
{
  "mcpServers": {
    "codebase-memory-mcp": { "command": "/path/to/codebase-memory-mcp" }
  }
}
```

Then, in a session: `index_repository` on the repo root. It writes, and it takes minutes.

**2. A language server, via Claude Code's LSP tool** — `"env": { "ENABLE_LSP_TOOL": "1" }` in
`settings.json`, plus a server for your stack (the `typescript-lsp` and `csharp-lsp` plugins in the
official marketplace are the easy path). LSP is what the skills fall back to when the graph looks
stale or ambiguous, and `findReferences` is the only reliable way to count call sites.

Without either one, the skills still tell you to degrade out loud and treat every count as a lower
bound — but you are getting a fraction of the value.

## Install

```
/plugin marketplace add SpectralAngel/ai-plugins
/plugin install code-change-discipline@ai-plugins
```

Restart the session so the hooks load.

## Turning the hooks off

The plugin injects text into every session and every subagent. If you want the skills but not the
nagging, disable the plugin and copy `plugins/code-change-discipline/skills/` into
`~/.claude/skills/` by hand, or fork and delete `hooks/hooks.json`. There is no setting that keeps
the skills and drops the hooks.

## Language servers — a gotcha worth knowing

`csharp-ls` searches its **working directory** recursively for solutions and never walks upward from
the file being edited. Given several it picks one arbitrarily and every request silently returns
"No symbols found". Start C# sessions in a directory with exactly one solution beneath it — never in
an umbrella folder containing several. `csharp-ls --diagnose --loglevel info` prints which one it
loads, without starting a session.

This is the class of failure the skills care about: not an error, just empty results that look like
an answer.

## Not shipped here

codebase-memory-mcp has its own `hook-augment` subcommand, wired as a `PreToolUse` hook on
`Grep|Glob`, which adds graph context to searches the agent runs anyway. It belongs to that project,
not this plugin. Wire it yourself if you want it.

## Other agents

`AGENTS.md` in this repo states the same discipline without any Claude Code or MCP tool names, for
agents that read `AGENTS.md` rather than the Agent Skills format. The `SKILL.md` files are plain
Markdown with YAML frontmatter and are readable by any tool that supports the format.

## License

MIT. See [LICENSE](LICENSE).

#!/usr/bin/env bash
# SessionStart hook: point at the code-change-discipline skill.
# Shipped by this plugin, so a plugin update carries changes to it.
# Deliberately names no tool parameters: signatures drift, and a half-accurate
# tool list is what teaches the model to skim. The skill is the source of truth.
cat << 'REMINDER'
CRITICAL — before your first code search and before your first edit:

Invoke the `code-change-discipline` skill (Skill tool, skill: code-change-discipline) and follow it.
It is not optional and it is not size-gated: a one-line fix uses the same ladder as a migration.

If you do not, the minimum is: never use Grep or Glob to find code, and never Read a large file in
order to search it. Use codebase-memory-mcp — list_projects (match the repo by root_path) →
search_code → search_graph → get_code_snippet — then LSP as the tiebreaker, trusting it over the
graph. `project` is required on every codebase-memory-mcp tool. Grep, Glob and Read are for text,
configs and non-code files, and you always Read a narrow window before you Edit.

If the repo is not in list_projects, say so out loud before falling back to grep.
REMINDER

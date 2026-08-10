#!/usr/bin/env bash
# SubagentStart hook: point subagents at the code-change-discipline skill.
# Shipped by this plugin, so a plugin update carries changes to it.
# SubagentStart injects context via JSON additionalContext, not plain stdout.
# The payload MUST stay on one line: raw newlines break the JSON and invalid JSON is dropped silently.
cat << 'REMINDER'
{"hookSpecificOutput":{"hookEventName":"SubagentStart","additionalContext":"Before your first code search or first edit, invoke the `code-change-discipline` skill (Skill tool, skill: code-change-discipline) and follow it — it is not size-gated. If you cannot: never use Grep or Glob to find code and never Read a large file in order to search it; use codebase-memory-mcp (search_code -> search_graph -> get_code_snippet; `project` is required on all of them), then LSP as the tiebreaker, trusting it over the graph; Read a narrow window before you Edit; and know the test count before and after. Grep, Glob and Read are for text, configs and non-code files."}}
REMINDER

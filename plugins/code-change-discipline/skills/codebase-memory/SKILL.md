---
name: codebase-memory
description: "Use the codebase knowledge graph for structural code queries. Triggers on: explore the codebase, understand the architecture, what functions exist, show me the structure, who calls this function, what does X call, trace the call chain, find callers of, show dependencies, impact analysis, dead code, unused functions, high fan-out, refactor candidates, code quality audit, graph query syntax, Cypher query examples, edge types, how to use search_graph. For the order to use these tools in while changing code, and for LSP, see code-change-discipline."
---

# Codebase Memory — Knowledge Graph Tools

Graph tools return precise structural results in ~500 tokens vs ~80K for grep.

> **Scope.** This skill is the *reference*: which tool answers which structural question, graph
> query syntax, edge types, gotchas. The *procedure* for changing code — what order to use these
> tools in, when to fall back to LSP or grep, how to edit and how to verify — lives in
> `code-change-discipline`. Query semantics go here; workflow goes there.

**`project` is required on every tool except `list_projects`.** Get the exact string from
`list_projects` by matching `root_path`; the names are inconsistent between projects.

## Quick Decision Matrix

| Question | Tool call |
|----------|----------|
| Who calls X? | `trace_path(project=…, function_name="X", direction="inbound")` |
| What does X call? | `trace_path(project=…, function_name="X", direction="outbound")` |
| Full call context | `trace_path(project=…, function_name="X", direction="both")` |
| Find by name pattern | `search_graph(project=…, name_pattern="...")` |
| Find by meaning | `search_graph(project=…, query="...")` (BM25) |
| Dead code | `search_graph(project=…, max_degree=0, exclude_entry_points=true)` |
| Cross-service edges | `query_graph(project=…, query=…)` with Cypher |
| Impact of local changes | `detect_changes(project=…)` |
| Risk-classified trace | `trace_path(project=…, function_name="X", risk_labels=true)` |
| Text search | `search_code(project=…, pattern=…)` or Grep |

## Exploration Workflow
1. `list_projects` — find the repo by `root_path`, copy the `name` verbatim
2. `get_graph_schema(project=…)` — understand node/edge types
3. `search_graph(project=…, label="Function", name_pattern=".*Pattern.*")` — find code
4. `get_code_snippet(project=…, qualified_name="project.path.FuncName")` — read source

## Tracing Workflow
1. `search_graph(project=…, name_pattern=".*FuncName.*")` — discover exact name
2. `trace_path(project=…, function_name="FuncName", direction="both", depth=3)` — trace
3. `detect_changes(project=…)` — map git diff to affected symbols

## Quality Analysis
- Dead code: `search_graph(project=…, max_degree=0, exclude_entry_points=true)`
- Refactor candidates by connectivity:
  `search_graph(project=…, min_degree=10, relationship="CALLS")` — degree here is **undirected**
  and `search_graph` has **no `direction` parameter**. To separate callers from callees, take the
  ranked names and run
  `trace_path(project=…, function_name=…, direction="inbound"|"outbound", depth=1)`.

## 14 MCP Tools
`index_repository`, `index_status`, `list_projects`, `delete_project`,
`search_graph`, `search_code`, `trace_path`, `detect_changes`,
`query_graph`, `get_graph_schema`, `get_code_snippet`, `get_architecture`,
`manage_adr`, `ingest_traces`

## Edge Types
CALLS, HTTP_CALLS, ASYNC_CALLS, IMPORTS, DEFINES, DEFINES_METHOD,
HANDLES, IMPLEMENTS, OVERRIDE, USAGE, FILE_CHANGES_WITH,
CONTAINS_FILE, CONTAINS_FOLDER, CONTAINS_PACKAGE

## Cypher Examples (for query_graph)
```
MATCH (a)-[r:HTTP_CALLS]->(b) RETURN a.name, b.name, r.url_path, r.confidence LIMIT 20
MATCH (f:Function) WHERE f.name =~ '.*Handler.*' RETURN f.name, f.file_path
MATCH (a)-[r:CALLS]->(b) WHERE a.name = 'main' RETURN b.name
```

## Gotchas
1. `search_graph(relationship="HTTP_CALLS")` filters nodes by degree — use `query_graph` with Cypher to see actual edges.
2. `query_graph` has a **100,000-row ceiling** (optional `max_rows`), not 200 — but it has no
   offset, so put `LIMIT` in the Cypher for broad queries. For counting, prefer `search_graph`
   with degree filters and read `total` off the response.
3. `trace_path` needs exact names — use `search_graph(project=…, name_pattern=...)` first.
4. `trace_path(direction="outbound")` misses cross-service callers — use `direction="both"`.
   Note `direction` belongs to `trace_path` alone; `search_graph` has no such parameter.
5. **Pagination differs per tool.** `search_graph` defaults to `limit=200` and paginates: check
   `has_more`, re-call with `offset += limit`. `search_code` defaults to `limit=10` and has
   **no `offset` and no `has_more`** — detect truncation by comparing `total_results` (deduped
   functions) and `total_grep_matches` (raw hits) against `limit`, then raise `limit` or narrow
   with `file_pattern` / `path_filter`.
6. `search_graph(query=…)` **ignores `name_pattern`** when both are given. `semantic_query` must be
   an **array** of strings, and returns hits under `semantic_results`, not `results`.

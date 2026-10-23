---
name: sweeping-change
description: "Execute a large pre-planned change across a big codebase using subagents, a code knowledge graph and LSP, with a living plan document. Triggers on: execute this plan, run the migration plan, apply this refactor everywhere, migrate N sites, sweep the codebase for X, rename across the whole repo, localize/instrument/convert every call site, work through this audit, large multi-site refactor, hundreds of throw sites, fan out agents over slices. Also use when a plan or audit document already exists and the job is to carry it out. Covers only what changes when work outgrows one context — the per-change discovery, editing and verification rules live in code-change-discipline and apply at every size."
---

# Sweeping change

For changes that touch more sites than fit in one context: migrations, cross-cutting refactors,
audits carried out to completion. The unit of work is a **slice**, executed by a subagent with a
fresh context, verified by the orchestrator, and recorded in a shared document.

**Before anything else, invoke the `code-change-discipline` skill** (Skill tool,
`skill: code-change-discipline`). It owns discovery, LSP, the editing protocol and verification for
every change at every size. This skill owns only what changes when the work stops fitting in one
context. Do not restate its rules here — put its name in every agent brief instead.

## When to fan out — this is about agent count, not about discipline

Fan out when the change spans **more sites than you can hold** — roughly 50+ edit sites, or any job
where reading the relevant code would itself exhaust the window.

**Do not fan out** for a change you can complete in one pass. Spawning agents for a ten-site rename
costs more than it saves and adds a verification burden. Scale the fan-out to the work: most jobs
justify two or three agents, and only a migration spanning hundreds of sites justifies dozens.

**This threshold gates subagents, worktrees and the plan document — nothing else.** The discovery
ladder, LSP-as-tiebreaker, the narrow-window edit protocol and test-count verification apply at
every size and are never "too much process for a small change". A ten-site rename still follows
`code-change-discipline`; it just does not spawn agents.

## 1. Treat the plan as a hypothesis, not a spec

A plan or audit handed to you is the best available guess, and it will be **wrong in specific,
checkable ways**. Assume it undercounts, and by margins that are routinely an order of magnitude
rather than a few percent.

Instruct every agent to **re-derive its own inventory** and treat the plan's numbers as lower
bounds. The techniques that actually produce ground truth, in order of reliability:

1. **Reflection over the built artifact** — enumerate types/members and inspect their attributes.
   Catches custom subclasses, inherited members, and parameters that text search cannot see.
2. **A guard's own regex**, reused verbatim, so the scan and the enforcement cannot disagree.
3. **LSP `findReferences` / `goToImplementation`** for call sites and interface implementors.

Grep is the least reliable and should not be how a count is established.

Plans also contain design claims that are simply false — including ones that are architecturally
impossible, and ones that would ship a silent no-op past a green build. **An agent that finds the
plan wrong and says so is doing the job correctly.** Say that in the brief.

## 2. The execution log is what makes corrections compound

Keep one document — the plan itself is ideal — with an **execution log near the top**. Every agent
reads it before starting and appends its findings before finishing. State explicitly that the log
**overrides the plan body** where they disagree.

Without this, each agent rediscovers the same traps independently. With it, a later slice starts
already knowing that a particular helper silently skips part of its input, or that a base-type
change stops an upstream `catch` from catching.

Record in the log, at minimum:
- corrected counts and inventories
- any plan claim found false, and what is true instead
- decisions and conventions later slices must follow
- the verification milestones (§5) and the discovered test count
- hazards that cost time (environment quirks, misleading tooling)
- what was deliberately **not** done, and why

## 3. The agent brief

Most of a brief is reusable. Adapt the bracketed parts:

```
## NON-NEGOTIABLE WORKING PRACTICES

**Your first action is to invoke the `code-change-discipline` skill** (Skill tool,
`skill: code-change-discipline`) and follow it. Do not search anything before you have.

If that skill is not available to you, the minimum is: this codebase is large — **do not use Grep
or Glob to find code, and never Read a large file in order to search it.** Use codebase-memory-mcp
(its own `codebase-memory` skill is the tool reference), watch every response for silent truncation,
and remember that `search_code` treats patterns literally unless `regex=true` and `trace_path`
excludes tests unless `include_tests=true`. **LSP is the tiebreaker — trust it over the graph.**
Read(offset, limit) a narrow window, then Edit with a tight old_string.

**Before you cite a path, call `check_index_coverage` on it** — once, batched over every path your
conclusion rests on. A clean result means no recorded gap, not proof of completeness; where coverage
is partial, skipped, excluded or stale, read that range directly and say so.

Project name (exact): <PROJECT>. `project` is required on every codebase-memory-mcp call. Confirm
anything load-bearing with LSP before editing.

**Never Read whole:** <the two or three largest files in scope>.

**Test count (from the runner's discovery mode, not a run):** <N> tests <plus any double-counting
quirk in the runner>. Track it as a number that must be accounted for, not merely "green". Do not
run the suite before editing. When your slice is done, run the build and the tests covering the
files you touched, once, and report both counts. Never revert work to replay red-green.

**An agent that finds the plan wrong and says so is doing the job correctly.**
Append your findings to the execution log at <path> before you finish.
```

Then add, per slice: the scope, the verification commands, and commit conventions.

Ask for a report that names **which plan claims turned out false** — that is the most valuable
thing an agent produces, and asking for it explicitly changes what comes back.

## 4. Parallelize on disjoint files, serialize on shared ones

Slices that append to the **same file** — a shared catalog, a constants file, a resource bundle —
cannot run concurrently even when their edit sites are in different files. Serialize those.

codebase-memory-mcp ships its own read-only agents — `codebase-memory-scout` (fast, provisional),
`codebase-memory` (task-directed) and `codebase-memory-auditor` (bounded full verification) — plus
`--tool-profile=analysis|scout` to restrict the surface. Use them for investigation slices; they
cannot edit.

For genuinely disjoint scopes, use **git worktrees**, and note:
- `isolation: "worktree"` operates on the primary working directory. In a monorepo whose **parent
  is not a git repo**, create worktrees on the **subrepo** yourself: `git worktree add <path> -b <branch>`.
- Put them **outside any syncing folder** (Dropbox, Nextcloud, iCloud) — sync races corrupt the index.
- Give each agent an explicit, disjoint file scope, and tell it which paths another agent owns.
- Have agents commit on their branch and **not** merge; the orchestrator merges, verifies, then
  removes worktrees and deletes branches.
- Gitignored config (local settings, env files) does not exist in a fresh worktree — copy it in.

## 5. Verify the agents

The per-change verification rules are in `code-change-discipline` §5 and apply to every slice.
On top of them:

- **Each agent tests its own slice in its round** — build plus the tests covering its files. The
  orchestrator does not rerun the suite after every slice or merge.
- **After a merge, build only.** It is cheap and catches a merge that is clean textually but broken.
- **Run the full suite at milestones** fixed in the plan document when the work is sliced: the end
  of a wave of merged slices, before a shared-file slice later slices build on, and before the
  final report. Run it yourself — a completion report is not evidence — and check the total
  against the discovered count. If a milestone run fails, bisect over that wave's merges rather
  than rerunning every slice.
- **Reports are usually accurate but occasionally wrong**, and the wrong ones are confident.
- **The orchestrator is not the reliable narrator by default.** It will confidently misread tooling
  output — a debugger's synthetic placeholder, a mock's canned response — as production behaviour.
  An agent that checks the runtime directly can be right where the orchestrator is wrong.

## 6. Known failure modes

- **A stalled agent is not lost work.** If it died after editing but before verifying, the edits are
  on disk. Check `git status`, run the gates, review the diff shape, and commit if sound — far
  cheaper than re-running the slice.
- **Driving a UI while another agent edits the code** causes hot reloads that bounce navigation
  mid-interaction. Finish the edits first.
- **A production build can clobber a running dev server's shared output directory**, leaving it
  serving a stale bundle silently.
- **Structural guards are the real deliverable.** Where one layer is enforced by a whole-directory
  scan and another by a hand-maintained file list, sites survive an entire migration untouched in
  the hand-maintained layer. When a slice finds a gap, ask what guard would have caught it, and add
  that.

## Anti-patterns

- Spawning agents for work that fits in one context.
- Passing the plan's counts through to the brief as targets rather than lower bounds.
- Letting two agents commit to the same repo concurrently.
- Accepting "all tests pass" without knowing what the number should be.
- Running the full suite before any edit just to learn the count, or after every merge.
- Reverting finished work to replay red→green.
- Reporting a residual as a finding instead of closing it. If it is in scope and safe, finish it;
  if you leave it, say plainly why and what would make it doable.

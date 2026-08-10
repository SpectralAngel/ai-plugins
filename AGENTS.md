# Working on an existing codebase

Rules for any coding agent, stated without reference to a particular tool. The Claude Code packaging
of these — three skills and two enforcement hooks — is in [`plugins/`](plugins/).

They apply to **every** change in an existing repository. Size decides whether you split the work
across agents; it never decides whether you verify.

## 1. Do not grep to find code

Text search over a large repository returns hundreds of unranked hits and no structure. It will
exhaust your context before you have changed anything, and it cannot tell you which function a hit
lives in.

Use, in this order, whatever your environment actually provides:

1. **A structural index** — a code knowledge graph or symbol database that returns the *containing
   symbol*, not just the line.
2. **A language server** — `findReferences`, `goToDefinition`, `goToImplementation`, call hierarchy.
3. **Disciplined grep**, last: file list first (`--files-with-matches`), then one narrow pattern with
   line numbers.

Never read a large file in order to search it. Text search is for prose, configs and non-code files.

## 2. Detect silent truncation before you quote a count

Every search tool has a result limit, and most of them apply it without saying so. Before you state
a number, check the tool's own signals — total-versus-returned, a has-more flag, the limit you
actually passed.

**A count taken from a truncated response is not a count.** State the number *and* how you got it,
so a reader can tell a measurement from a guess.

## 3. The language server is the tiebreaker

When the index and the language server disagree, the language server wins. Indexes resolve calls by
name and collapse same-named methods from different types into one node, so verify whenever a name
is shared, and always before an edit whose correctness depends on who calls what.

If no language server exists for the language: probe once, then stop. Do not retry it symbol by
symbol. The index becomes authoritative, and any count must come from a script or regex reused
verbatim rather than from eyeballing a list.

## 4. Say which rung you are on

If the repo is not indexed, or there is no language server, or neither — say so in one line before
you rely on any number, and treat every count as a lower bound. Degrading silently is how a guess
gets reported as a measurement.

## 5. Read a narrow window, then edit

Locate the site precisely, read a small window around it, then edit with a tight, unique anchor.

Line numbers from a plan, an earlier session, or an index are **not durable — re-derive them.** Never
edit from a cached snippet without confirming the current text on disk; an index can be many commits
behind the working tree.

## 6. Verify by number, not by colour

- Know the test count **before** you start. Track it as a number that must be accounted for, not
  merely "green". An unexplained delta is a finding in either direction.
- Run the build and the suite yourself. A report that it passed is not evidence.
- Diagnostics captured mid-edit look exactly like real failures and are frequently stale. Confirm
  against a real build before acting on them.
- **Tests can pin a bug as correct.** An assertion can document broken behaviour as expected, so a
  passing suite is not evidence that the behaviour is right.
- You will be wrong too. When you find you stated something false, correct the record plainly.

## 7. Treat a plan or audit as a hypothesis

A plan handed to you is the best available guess, and it will be wrong in specific, checkable ways.
Assume it undercounts — routinely by an order of magnitude, not a few percent — and re-derive every
inventory yourself. Plans also contain design claims that are simply false, including ones that
would ship a silent no-op past a green build.

**An agent that finds the plan wrong and says so is doing the job correctly.**

## 8. If the work outlives one context, write the corrections down

A second session, a subagent, or a compaction loses everything you learned that is not on disk. Keep
one document with an **execution log near the top** that **overrides the plan body where they
disagree**: corrected counts, plan claims found false, decisions later work must follow, hazards that
cost time, and what was deliberately not done and why.

Without it, every agent rediscovers the same traps independently.

## Anti-patterns

- Grepping first "just to have a look".
- Quoting a count off a response that hit its limit.
- Retrying a language server after it has already reported no support for that language.
- Reading a whole file to change three lines of it.
- Spawning parallel agents for work that fits in one context.
- Accepting "all tests pass" without knowing what the number should be.
- Reporting a residual as a finding instead of closing it. If it is in scope and safe, finish it; if
  you leave it, say plainly why and what would make it doable.

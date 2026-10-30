# Intake: cloudflare/security-audit-skill

2026-10-30. Read at commit `c1c8a8c` (2026-09-14), MIT. Not run; read only.

**What it is.** A skill that turns a coding agent into a security auditor of application code:
six phases (recon, coverage-led hunting, adversarial validation, structured output, independent
re-verification, report), a coverage ledger, a findings schema, and two zero-dependency Node
validators. It is not a skill scanner. Its subject is code, not the instruction layer, and it
assigns severity, which Walkdown never does.

**What is worth taking:** a few attack shapes from its AI and supply-chain guides that
Walkdown's stages can see statically, two pieces of method (the coverage ledger and
"carry a prior verdict only on unchanged source"), and the skill itself as test material.
Most of its guidance is for running and probing code, which Walkdown does not do.

Paths below are relative to `skills/security-audit/` in that repository.

---

## Items

Each item: what to add, where the idea comes from, what Walkdown has today, and where it would go.
Ordered by value for effort.

### CF-1. Code an install runs that can change after review (pin state)

- **Source.** `SUPPLY-CHAIN-AND-RELEASE.md:24` (mutable and unbound build inputs: floating
  tags, branches, downloaded tools) and `:58` (plugin and extension trust expansion: install or
  update hooks that run before any check).
- **Today.** `RL.branch-ref` matches `@main` / `@latest` in text, and `E.install-global` matches
  `npx -y`. Both are phrase hits. `struct.mcp` records each server's command but not whether
  the thing it runs is pinned.
- **Add.** A pin state for everything the host runs by name: MCP server commands (`npx -y pkg`,
  `uvx pkg`, `bunx`, `docker run image` or `:latest`, `pip install pkg` with no `==`), hook
  commands, and install lines in model-read text. Values: `exact` (version or digest),
  `range`, `none`. Proposed check `pin.state` in stage 1 (configs) and stage 4 (instruction
  text), and stage 5 pairs it: an unpinned MCP server is code that changes after review, and it
  carries outside input into the trifecta.
- **Report wording.** "Runs code it downloads each time, at whatever version is current."
  Capability, not fault.
- **Fixture.** `.mcp.json` with one exact, one range, one bare, one `@latest`, one docker
  image with no tag. Hooks with `npx` both pinned and unpinned.

### CF-2. Names that collide (MCP servers, tools, skills, commands)

- **Source.** `AI-AND-LLM.md:56` (MCP server and tool identity confusion: two servers claiming
  the same tool identity; routing by an attacker-chosen name).
- **Today.** `trig.overlap` measures how many words two descriptions share. Nothing compares
  names.
- **Add.** `trig.name-clash`: within the repository, two MCP servers, skills, agents, or commands
  with the same name; and against a dated list of host built-ins (slash commands such as
  `/review`, `/init`, `/security-review`; well-known MCP server names such as `github`,
  `filesystem`), a name that matches a built-in. The list lives beside `hosts.yaml` with a date.
- **Open.** What each host does on a clash (which one wins) has to be checked against host docs
  before the report says anything about it. Until then, report the clash only.

### CF-3. A coverage ledger behind stage 7

- **Source.** `SKILL.md:105` ("Never imply that one run exhausts the target"), `:115` (a scoped
  run must present itself as partial), and `RECONNAISSANCE.md:90-156` (one unit per surface ×
  boundary × class, each with a status, checked by a validator).
- **Today.** Stage 7 lists what was skipped: unread files, missing optional tools, the
  test-data rule, standing limits. It is a list of gaps, not a table of what was covered.
- **Add.** `data/07-ledger.json`: one row per (model-read file, check group 4a to 4d, stage 2
  reading), status `examined`, `blind` (with the reason: non-English, unread, image with no
  OCR, past a size limit), `set-aside` (human, test data), or `not-built`. A small validator
  in the grader: every model-read file has a row for every group, and no row says `examined`
  where stage 2 says unread. Then "nothing found" in a report can say per file what it rests on.
- **Why it matters.** A zero is only as good as what was looked at. The ledger turns that rule
  into something a test can check.

### CF-4. Carried marks when the context changed

- **Source.** `SKILL.md:98` (a prior verdict carries only when the *relevant* source is
  unchanged; a matching source ref is not enough).
- **Today.** Marks carry over by the flagged text (`marks.SPEC.md`), so an unchanged line keeps
  its mark. The line can stay the same while what surrounds it changes: the skill that owns it
  gains Bash, a hook starts running its script, a trifecta leg switches on.
- **Add.** When `changes.md` shows that the owning skill's grants, hooks, or legs changed, a
  carried mark keeps its value but is shown as "carried; what this skill can do has changed
  since". The reader decides. Read `marks.SPEC.md` first: the fix may be a new key part rather
  than a new flag.

### CF-5. Shipped outside facts, named one by one (from "needs_validation")

- **Source.** `SKILL.md:146` (respect source visibility: when a decisive fact is outside the
  source, do not assume it either way; name the exact missing fact).
- **Today.** Stage 7 states the standing limit (static only). Individual findings that depend
  on something outside the repository do not say what that is.
- **Add.** Per finding, in stage 7: the content at a URL a remote-load phrase fetches (named,
  never opened); the code of a package an MCP server or hook downloads; a host setting a
  `cap.limit` read-only claim depends on. Each one is a row: "not examined: <fact>, needed for
  <finding>".

### CF-6. Repeat the sweep, and measure what a second pass adds

- **Source.** `README.md:98` ("a single run found roughly half of the vulnerabilities that
  repeated runs found in total").
- **Today.** One sweep per run. Measured repeat variance on labels is about 0.1.
- **Add.** An experiment, not a feature: run the sweep three times on the MODEL-ACCURACY sets
  and record what the union adds over one pass, and at what cost in false flags. Build
  `--sweep-passes N` only if the union earns it. Record the result in `MODEL-ACCURACY.md`.

### CF-7. Use the skill itself as test material

- Thirteen model-read companion files dense with attack vocabulary used as description
  ("prompt injection", "exfiltration", "credential", "bypass"). It is the self-audit problem
  (quoted threats in docs) in someone else's repository.
- **Use 1.** Audit it, and add it to the corpus behind `baserates.json`.
- **Use 2.** Draw stage 6 labeled lines from it: most hits should label `description`. MIT,
  so excerpts are allowed; add its license to `THIRD-PARTY-NOTICES.md` and a line to
  `CREDITS.md` under test data.
- **Use 3.** It asks for a lot (parallel subagents, writes under `~/security-audit-skill/`,
  builds and tests in a sandbox) with no `allowed-tools`. A good real case for `ask.tools` and
  `fit.missing`.
- Coordinated disclosure applies as for any audited repository if anything live turns up.

### CF-8. Renderer limits (small)

- **Source.** `SKILL.md`, "Universal execution safety": no network, empty environment, read-only
  inputs, and explicit CPU, memory, and time limits for anything that processes target files.
- **Today.** `render_html.py` has a 10 s page-load timeout, scripts off, nothing fetched.
  PDFium and Tesseract run on untrusted files with no stated memory or time limit.
- **Add.** A time and memory cap per file for PDF drawing and OCR, with a hit listed in stage 7
  as unread ("stopped at the limit"). Check the stage 2 specs for what is already bounded.

---

## Already covered (agreement, no change)

| Their rule | Walkdown's |
|---|---|
| A guardrail prompt is not a security boundary (`AI-AND-LLM.md:14`) | `cap.limit`: read-only wording is backed, contradicted, or "stated in the text only" |
| The agent that checks a finding never found it (README, design principles) | Detection and judgment never happen in the same step |
| Prompt injection alone is not a finding; require a boundary (`AI-AND-LLM.md:10`) | Capability, not intent; the trifecta |
| Unbounded delegated action loops (`AI-AND-LLM.md:48`) | `fit.loop` |
| Persistent memory poisoning (`AI-AND-LLM.md:28`) | `E.memory`, the persistence grant |
| Sub-agent trust inheritance (`AI-AND-LLM.md:53`) | `fit.inherits`, `cap.posture` |
| Approval that covers more than one action (`AI-AND-LLM.md:42`) | `A.scope` ("confirm once", "covers all"), `L.skip-confirm` |
| Build-context inclusion: secrets and dev files shipped (`SUPPLY-CHAIN-AND-RELEASE.md:30`) | `secret.found`, `cap.ship` |

## Not taken

- **Severity anchors** (critical to informational, `SKILL.md:150`). No score, by rule.
- **The sandbox and write-isolation procedure.** Walkdown runs no target code.
- **Hunter waves, budgets, and verifier agents.** Walkdown's model holds no tools; the
  orchestration has nothing to attach to.
- **The domain guides for application code** (web, cloud, binary, mobile, messaging). Out of
  scope: they are about the code a skill might be asked to review, not the skill.

## Credit

If any item lands: a line in `CREDITS.md` under prior work, with the repository link and what
was taken.

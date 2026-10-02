# Customers — who uses this, and what they get

Every other document in this folder answers *how the audit works*. None answers
*who is holding the report and what they do next*. This one does.

The project was built as a puzzle-solver: point it at an artifact, surface what
the instruction layer asks for and what installing it grants. That is the engine.
This file names who the engine is for, because the report has to fit the reader,
and the two readers act on the same finding in opposite directions.

**Revised 2026-09-24: the builder is the primary customer.** The adopter is still
served but no longer designed for. Why, in one line: the no-verdict stance *fits*
the builder and *fights* the adopter. The builder already knows the skill's
intent, so a capability report plus the builder's own purpose makes a complete
judgment, and nobody has to fake one. The adopter wants a verdict; the tools that
give one (SkillSpector's SAFE / CAUTION / DO NOT INSTALL, see THREATS.md Prior
art) will win that reader, and that is accepted rather than fought.

The report answers two things, in this order: **here is what this touches**, and
**here is what could be an issue**. Never "this thing is bad."

---

## The one-line value

Skills, agents, MCP servers, and CLAUDE.md files are plain-English instructions
loaded into a model and run with the user's own permissions. No sandbox, no
review, no signing. A code scanner sees nothing, because the payload is a
sentence, not code.

Walkdown reads that layer and reports, cited to file and line, two things:
what the text asks the model to do, and what installing it grants. It reports
**capability and surface, never intent**, and it renders **no score** — the last
judgment stays with the reader. What it adds that a lone reading cannot: the base
rate. It tells you which patterns are normal in a clean repo and which are rare
enough to be worth your time.

---

## Customer 1: The builder (primary)

**Who.** Someone who wrote a skill, agent, or skill repository and is about to
ship it, or has shipped it and wants to keep it clean. Includes the ICM cohort
and anyone writing context files who wants to know whether their files hold
weight or are decoration burning context.

**Why they would come (the hook, untested).** Most builders are not asking for a
security audit; many are hobbyists shipping free skills, and no felt pain means no
pull. The pain that now exists: curated marketplaces and verification programs
put automated scanners in front of submission (NVIDIA Verified Agent Skills runs
SkillSpector). Those scanners flag a skill's own stated function at high rates
(~80% static false positives in the TDS evaluation). The builder's question
becomes "what will get flagged, and is it actually a problem?" Walkdown is the
**explainer, not another gate**: CI gates already exist (Cisco pre-commit,
SkillSpector SARIF), so a CI integration is not the first thing to build.

**The situation.** They wrote it with no bad intent. But intent is not what
installs. A helpful line like "fetch and follow instructions from this URL" is
unauditable the moment it ships, because the instructions are not in the artifact
anyone reviewed. Careless is far more common than hostile, and the author cannot
see their own blind spot by rereading their own prose.

**What they get.** A pre-flight check on the instruction layer their tooling
cannot see: remote instruction loading, definition conflicts, hidden or
zero-width text, capability sprawl, payloads sitting in subagent templates or
error paths, a permission-widening flag they pasted into the README. Each finding
is a location in their own files, not an accusation.

**How they use it.** Run it on their own repo before publishing, and on the diff
at each release. This is the dogfooding case: run Walkdown on Walkdown
before it ships, and Case 002 (the Plumbline self-audit) is exactly this customer.

**What they do with a finding.** They fix it or remove it. For this reader the
report is a to-do list. They own the artifact, so a located problem is an action,
not a decision.

**What else they get: recommendations.** Added 2026-09-24. Builder-facing only,
under the rules in "Recommendations: the rules" below. A recommendation names
a narrower way to do the same thing; the builder decides whether it applies,
because only they know what the skill is for.

**What it does not give them.** A clean result is not a certificate. "Clean"
means these passes found nothing, not that the skill is safe. And it does not
grade craftsmanship or whether the skill works — only what its text asks for and
what installing it grants.

---

## Customer 2: The adopter (secondary; served, not designed for)

*Revised 2026-09-24.* Everything below still holds: the adopter can read the same
report and gets the same facts. What changed: the overview page is no longer
written for this reader, and no part of the report is shaped to answer their
go / no-go. An adopter who wants a verdict is better served by a scanner that
gives one, and the report says so plainly rather than half-imitating one.

**Who.** Someone deciding whether to install a skill, or a team or platform
gatekeeping what gets installed across an organization. They did not write it and
cannot ask the author to explain every line.

**The situation.** They are about to grant a stranger's English text the right to
run with their own permissions, against their own repos and data. The trust
signal they have — reputable author, official marketplace — is exactly the signal
that stops anyone from looking, and that is the signal every real incident abused.
They need to see the instruction layer before they adopt, not after.

**What they get.** The capability posture in one line (does it touch private
data, is it exposed to untrusted content, can it talk out), the surface an install
grants, and the points of attention worth a human's eyes — each a file and line
they can open. Critically, they get the base rate alongside each count, so a
number reads as "32 hidden-text hits, 32 benign, the noise floor" rather than as
a scare figure. That is what lets them tell an abnormal repo from a normal one.

**How they use it.** Point it at a link or a local repo before installing.
Low-friction in, one overview page out: one screen, numbers with their
denominators, locations not verdicts. (The overview page is written for the
builder as of 2026-09-24; the adopter reads the same page.)

**What they do with a finding.** They do not fix it — it is not theirs. They
decline to install, ask the author, or report it through coordinated disclosure.
For this reader the report informs a go / no-go decision they make themselves.

**What it does not give them.** A verdict. There is no "safe / not safe" field,
no risk score, no letter grade, on purpose — collapsing locators into one number
is the failure this project exists to name. The tool surfaces and locates; the
adopter supplies the last judgment, because only they know what the skill is
supposed to do and what they would accept as normal.

---

## What both share

- **The input is the same and low-friction.** Point at a link or a local repo.
  Neither customer bends here.
- **Both bend at the end.** The report explains *why* something is flagged and
  hands over the location, but the reader still supplies the final judgment —
  "is this actually a problem for me?" — because the tool does not know the
  skill's intended purpose or what the reader would accept as normal. This is the
  deliberate seam, not a shortfall: the same commitment as "capability, not
  intent" and "no aggregate score."
- **Same artifact, two documents.** The overview page is the builder's one-screen
  read of what the skill touches and where to look; the full report is the fix
  list with every file:line and the recommendations. The adopter reads the same
  two documents. (See REPORTING.md Part A, revised 2026-09-24 to match.)
- **"Comprehensive" means the full report, never the first page.** The full
  report covers everything the passes found. The overview fits one screen. And
  comprehensive coverage is a later iteration: v1 ships the thinnest path that
  produces a real report (HANDOVER, Before you build).

---

## Recommendations: the rules

Added 2026-09-24. A recommendation is a judgment, so these rules keep it from
smuggling the verdict back in.

1. **Builder-facing only.** Never an install recommendation to an adopter. No
   "safe", "caution", "do not install", or anything that reads as one.
2. **Tied to a file and line.** Every recommendation points at the exact text it
   is about.
3. **Conditional on intent the builder supplies.** "If this skill does not need
   network access, `allowed-tools: WebFetch` (SKILL.md:12) can be removed." Not
   "this is dangerous."
4. **Name the narrower alternative.** Scope the tool, pin the URL, inline the
   remote instructions, declare the capability. Not just the problem.
5. **Never ranked.** Ordering recommendations by importance is a hidden severity
   score. Order by document position or group by capability surface.

**The plain-facts rule.** Some findings are genuinely alarming, and refusing to
say "bad" must not read as evasion. The answer is to state the fact in full,
plainly: "This text is invisible when rendered and instructs the model to send
X to Y." A fact can be damning without being a verdict. The report never adds an
adjective the fact does not carry on its own.

---

## Adjacent readers — value, but not customers

Named here so scope does not creep into serving them.

- **The research community.** The published cases, the taxonomy, and the base
  rates are useful to anyone studying this surface. That is the *body of work*
  (see notes.md), and its reader is not a user of the tool.
- **Platform and marketplace operators.** The trifecta-as-install-control idea
  (break one leg at install time; see RED-TEAM.md) is aimed at them. That is a
  recommendation this project can make, not a product it ships.

---

## Open questions this framing raises

Recorded here so they are not lost. None is decided.

**First, and it outranks the numbered ones: does a builder actually want this?**
Added 2026-09-24. The marketplace-scanner hook is a hypothesis, not evidence.
Case 003 written as a builder report is the test; if no builder would act on it,
the customer choice is wrong, not the report.

1. **Does the adopter ever state the skill's intended purpose up front?** If they
   did, a capability finding ("local files + internet") could be judged against
   what is expected instead of left entirely to the reader. Today the method
   takes no such input. Adding it would sharpen Customer 2's report; it also
   risks importing the author's own claims as ground truth, which the method
   otherwise refuses.
   *Partly resolved 2026-09-24 by the builder focus:* for the builder, the reader
   *is* the source of intent, so recommendations are written conditional on it
   ("if this skill does not need X…") and the builder resolves them. The facts
   sections still take no stated purpose as input, so the refusal to treat the
   author's claims as ground truth stands. Whether the builder should state
   purpose up front (so recommendations can be filtered) stays open.
2. **Build vs. buy for the hard-fact layer.** The deterministic checks
   (invisible-Unicode, secret scanning) likely exist as libraries. How much to
   wire in versus build is undecided, and it changes what either customer can run
   today. (Also in HANDOVER known gaps.)
3. **Who keeps the definition current, and is there a feed?** Both customers only
   get value while "what is dangerous" is up to date. Today that is the maintainer, by
   hand. Whether a public source exists to pull new attack classes from, or
   whether it is always manual, decides whether this scales past one maintainer.

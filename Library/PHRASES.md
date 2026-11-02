# Phrases

The sets of wording Walkdown's pattern table looks for, in its own words.

`THREATS.md` describes the classes. This file groups the pattern rows (`patterns.yaml`) into lettered
sets by the kind of wording they find. A set is a family of shapes, not a list of banned words.

**How to read this file.**

- Every hit is a locator, never a verdict. The phrases here also appear in clean repositories, so
  Walkdown records the benign count along with the hits. How often a pattern turns up across the
  audited repositories is measured in `baserates.json` and shown in a report as rare, uncommon, or
  common.
- Nothing here is a working instruction. These are descriptions of what to find.
- Patterns run case-insensitively, on text that has been folded first: invisible characters removed
  and look-alike letters normalized (`invisible.yaml`), so a keyword cannot hide by being split or
  disguised. A pattern is checked against a known positive before a zero from it is trusted.
- The letters are stable tags, like the class numbers. A set cites its class in its heading. Each
  entry ends with the pattern rows that cite it; a row can also cite a class in `THREATS.md`
  (a row may cite more than one place), and what a pattern row looks for in plain words is its own
  `plain` field.
- The phrase step (`02.4-phrases`) runs the sets in four groups: reaching out (K, and the credential and remote-loading
  rows), taking the wheel (L, A, B, H, I), changing the environment (E, C, D, J), and talking to the
  human (G). There is no set F: reader-limit evasion is measured by thresholds, not by wording, and
  is not a set of phrases.

## A. Claimed authorization and consent (class 13)

**What it is.** Wording that says permission already exists: the user has already approved or
configured something, installing counts as consent, a standing approval, a role or persona with
authority, one confirmation that covers everything after it, a made-up exchange in which the user
agrees, text formatted as the AI tool's own messages, and "tell the user, then carry on".

**Why it matters.** The model is told consent exists without anyone having been asked, and it cannot
check the claim.

**What Walkdown looks for.** Each of those claim forms. A skill's documentation often quotes the
tool's message formats as examples, so a hit on the mimicry shape is a locator to read.

**Patterns:** `A.dialogue`, `A.harness-mimicry`, `A.install-consent`, `A.notify-proceed`,
`A.persona-grant`, `A.prior-consent`, `A.role-authority`, `A.scope`, `A.standing`

## B. Definitional hijacking and defaults (class 14)

**What it is.** Wording that changes what an ordinary request means or what a blank contains: a
word redefined to include an action, a casual phrase from the user mapped to an action, a default
that names a destination, a rule that applies only when something is missing, a safety exception
("never, except ..."), a reassuring word beside a command, and a domain that imitates a placeholder.

**Why it matters.** The instruction that fires is the user's own request; the skill changed its
meaning. The absence rules fire on fresh repositories, where nobody is watching, and the exception
clause hides the payload behind a safety statement.

**What Walkdown looks for.** Redefinition verbs followed by a risky action, "when the user says X"
mapped to an action, defaults and absence rules with a destination, never-except clauses, safety
adjectives next to a command or script, and look-alikes of `example.com`. The safety words can be
checked against the script they describe, which is why they are worth a look.

**Patterns:** `B.absence`, `B.default-dest`, `B.lookalike`, `B.means`, `B.safety-adjective`,
`B.safety-exception`, `B.when-says`

## C. Second-order layers (class 15)

**What it is.** Text the skill hands to something else to carry out: the permission and model
settings in a skill or agent file, a subagent per item, a note addressed to the AI, instructions in a
code comment, instructions printed by a script or placed in an error message, text the model is told
to add to what it writes, and instructions for writing other skills.

**Why it matters.** It runs somewhere with less review and fewer guardrails: a subagent with every
tool, a script's output taken as fact, a footer that copies itself into other people's work.

**What Walkdown looks for.** The grant keys in frontmatter, "dispatch a subagent for each", notes
and comments addressed to an assistant, strings in scripts that carry a command or an instruction
(and the hook that would deliver them), and text telling the model to add a footer or to author
instruction files. The capability step (`02.5-capability`) pairs a script instruction with a hook that injects context.

**Patterns:** `C.boilerplate`, `C.comment-ai`, `C.emit-instruction`, `C.error-instruction`,
`C.fan-out`, `C.frontmatter-grant`, `C.note-to-ai`, `C.script-instruction`, `C.skills-author`

## D. Trust elevation (class 16)

**What it is.** Wording and settings that give text more authority than its source deserves: hooks
that fire when the conversation is compacted or on every tool call, hook output that adds to the
model's context, all-caps tag wrappers, "read the current version", and verification steps that are
really commands to run.

**Why it matters.** Text that arrives through the tool's own channel is weighted above file content,
and a hook fires at moments when the model remembers least of what the user allowed.

**What Walkdown looks for.** A hook matcher for compaction, a matcher that matches everything, a
context-adding field, pseudo-tags in loaded or emitted text, instructions to trust whatever is
current, and a verify step phrased as "run this".

**Patterns:** `D.additional-context`, `D.compact-matcher`, `D.current-version`, `D.match-all`,
`D.pseudo-tag`, `D.verify-run`

## E. Environment mutation (class 17)

**What it is.** Changes that outlast the task and reach outside the repository, and the widening of
permissions that goes with them. This set also holds the install and permission rows of class 7:
flags and settings that skip or widen permissions, variables that reroute traffic, git settings that
run something on every command, a registered tool server, installing packages or the skill itself
globally, memory and local settings files, connecting an account, an editor setting that runs a task
when a folder opens, and an environment variable set in prose.

**Why it matters.** One line changes where everything goes or what runs afterward. A skill rarely
has a reason to set a traffic-redirection variable, so a hit on that row is worth a look first.

**What Walkdown looks for.** Permission-skipping flags and allow-list settings, proxy, registry, and
base-address variables, git keys such as `insteadOf` and `core.hooksPath`, tool-server registration,
install commands (`E.install` for the project-local forms, `E.install-global` for the global and
plugin forms, which are class 7), copying a skill into the user's global folder, writing to memory
files, "connect your account", editor auto-run, and `export NAME=value` in prose (not in a script).

**Patterns:** `E.connector`, `E.editor-autorun`, `E.export`, `E.git-keys`, `E.install`,
`E.install-global`, `E.mcp`, `E.memory`, `E.perm-flags`, `E.redirect-var`, `E.self-install`

## G. Human-audience instructions and the inbound surface (class 19)

**What it is.** Wording aimed at the person reading the documentation, or at the agents of people who
visit the repository: install steps that tell a person to run the tool with permissions skipped, to
pipe a download into a shell, or to paste something into a terminal, requests to trust a folder, and
issue and contribution templates addressed to an AI.

**Why it matters.** It is the same file and the same layer with a softer target. A template in a
popular repository can instruct every contributor's agent.

**What Walkdown looks for.** Permission flags in README and install files, pipe-to-shell lines,
templates that say they assume an agent filed them, and imperatives in contribution files addressed
to the reader. The remaining rows of this class are in `THREATS.md`.

**Patterns:** `G.agent-template`, `G.contrib-imperative`, `G.perm-flags-docs`, `G.pipe-shell`

## H. Anti-review and audit-trail shaping (class 20)

**What it is.** Wording that shapes what gets read, said, or kept: that something is already reviewed,
an exact phrase the model must announce, an objection pre-empted before the model can raise it, a
warning that skipping a step will break things, deleting logs and plans, calling another skill
deprecated so it is skipped, claims of precedence, a self-attestation ("contains no telemetry"), a
loop with no stopping point, and an instruction to keep something from the user.

**Why it matters.** These remove the trail that makes an action reviewable. Many of them are ordinary
in legitimate skills, and several are noisy on their own, so the table narrows them to the phrase
forms and records which direction a precedence claim points.

**What Walkdown looks for.** The forms above. Capping the length of a reply is not flagged: models are
wordy, and a limit on a reply is ordinary.

**Patterns:** `H.anti-inspect`, `H.consequence`, `H.evidence`, `H.mandated-phrasing`, `H.precedence`,
`H.preempt`, `H.sabotage`, `H.self-attest`, `H.suppress`, `H.unbounded`

## I. Conditional activation (class 21)

**What it is.** Wording that makes behavior depend on a condition: which AI tool is running, a date,
a version, a first run or a later one, a repository, organization, or machine name, or a failure.

**Why it matters.** The reviewed behavior and the delivered behavior can differ. A harness
conditional is usually honest platform adaptation, and a hostile one fires only on the tool with the
loosest permissions.

**What Walkdown looks for.** "If you are running in ...", per-tool bullets, "after March 2026",
"version >= 2", "on the first run", "if the repository name is ...", and an error path followed by a
command, address, or token.

**Patterns:** `I.clock`, `I.environment`, `I.failure-path`, `I.harness`, `I.state`, `I.version`

## J. Harness-prohibited actions (class 22)

**What it is.** The actions AI tools commonly leave to the user, or ask the user to confirm first.
The prohibited tier (left to the user) includes entering credentials or payment details, creating
accounts, permanent deletion, financial transfers, changing security settings, and solving CAPTCHAs.
The confirm-first tier includes sending a message, publishing, buying, accepting terms, granting a
service access to an account, changing account settings, creating standing rules, and submitting
forms.

**Why it matters.** A skill that tells the model to do these without a confirmation asks it to take
an action that AI tools commonly leave to the user, or ask about first.

**What Walkdown looks for.** The wording that asks for each action, with the confirm-first rows
dropped when an ask or confirm is on the same line. `vocab.yaml` gives each row its tier and the
confirmation words the step "What the text asks for" checks for in the same instruction.

**Patterns:** `J.confirm-first`, `J.confirm-first-other`, `J.cookie`, `J.enter-secret`,
`J.irreversible`, `J.prohibited-other`, `J.saved-login`

## K. Destination and construction (classes 1 and 4)

**What it is.** Wording about where data goes and how an address is made, plus the markdown that can
carry text out of view: a destination named by reference, an address built from pieces, telemetry and
update checks, and link definitions, collapsed sections, hidden attributes, long alt text, and image
addresses with a slot for text in them.

**Why it matters.** There is no address for a search to find, so the destination or the carrier has to
be recognized by its shape. The telemetry words are common in ordinary documentation, so their hits
are mostly benign; the row is there to show where data goes home.

**What Walkdown looks for.** "The usual endpoint", "your team's webhook"; string concatenation,
`chr(`, `fromCharCode`, reversed strings; the telemetry words; link definitions to a web address,
`<details>`, a `hidden` attribute, a long `alt=`; and an image whose address carries a template slot.

**Patterns:** `K.assembly-code`, `K.dest-ref`, `K.md-carrier`, `K.telemetry`, `K.url-template`

## L. Instruction override and takeover (class 5)

**What it is.** The loud takeover shapes: a model told in plain text to drop what it was given,
forget it, take a new identity, accept "your real instructions", read a line dressed as a system
message, drop its rules, accept a fake end to the prompt, or treat one line as top priority.

**Why it matters.** It is the canonical injection. The strongest attacks do not use this wording, so a
zero here is not a safety statement, and a hit is a locator. Careless matching turns the set into an
intensity linter: legitimate skills use emphasis and precedence language, so every row is narrowed
and tested against benign twins.

**What Walkdown looks for.** "Ignore or disregard the earlier instructions", "forget everything",
override or supersede wording with an instruction-like object, "you are now ...", "here are your new
instructions", a `system:` line, "no restrictions" and rule suspension, "end of system prompt", and
"this is the highest priority". Suppression ("do not mention") is the companion and lives in set H.

**Patterns:** `L.context-end`, `L.forget`, `L.guardrail`, `L.identity`, `L.ignore`,
`L.new-instructions`, `L.override`, `L.priority`, `L.system-frame`

# Phrases — exact strings worth locating

Added 2026-09-04. Companion to THREATS.md. That file describes classes; this one
lists the literal strings and near-regex patterns that locate them.

Rules for this file:

- **Locators, never verdicts.** Every phrase here appears in clean repositories.
  The benign share is recorded where it was measured.
- **Nothing here is a payload.** These are detection strings. No entry is a
  working instruction, and none should be copied into a fixture without the
  inert-marking rule from HANDOVER.
- **Run case-insensitive, on NFKC-folded text with zero-width characters
  stripped.** A case-sensitive first run of these patterns on superpowers
  returned false zeros on at least three sets. See REVIEW-2026-09-04.md.
- **Validate every pattern against a known positive before trusting a zero.**
  A zero from an untested regex is not a measurement.
- Base rates below are hits on obra/superpowers v6.3.0 (195 files), counted
  case-insensitively, unless stated. "n/a" means not yet run.
- **Since 2026-09-29 the executable table is `stages/04-phrases/patterns.yaml`**
  (127 rows, each citing the row or THREATS bullet below it comes from). The
  stage 4 counts on the same superpowers copy are in "Stage 4 v1 measurement"
  at the end of this file; the per-row base rates below are the earlier hand
  counts, kept as history.
- **The live base rates (2026-10-01) are `stages/08-report/baserates.json`**, rebuilt by
  `stages/08-report/baserates.py` over every audited repository (outside human-facing files
  and test data), and shown in reports as rare / uncommon / common. Where the per-row numbers
  below disagree, that file is current.

**Where the sets run (2026-09-25).** The lettered sets below are all stage 4
(METHOD.md), by sub-group: **4a reaching out** K, E rollup (credentials, remote
loading); **4b taking the wheel** L, A, B, H, I; **4c changing the environment**
E, C, D, J; **4d talking to the human** G. Set F (reader-limit evasion) is
measurements, not phrases, and runs in stage 1. Letters are stable IDs, like
class numbers; they are called *sets* so they are not confused with the stage
sub-groups.

---

## A. Claimed authorization and consent (class 13)

| Pattern | Base rate | Note |
|---|---|---|
| `(user\|human\|owner) (has\|have) (already )?(approved\|authorized\|configured\|consented\|agreed)` | 0 | claimed prior consent |
| `constitutes (approval\|consent)` | 0 | install-as-consent |
| `standing (approval\|permission\|authorization)` | 0 | |
| `you (are\|have been) (authorized\|permitted\|allowed\|granted\|approved)` | 0 | persona grant |
| `you are (the\|a\|an) [a-z ]+ (and\|with) (standing\|full\|admin)` | n/a | role assertion carrying authority |
| `confirm(ation)? once` , `covers (all\|subsequent)` | n/a | consent scoping |
| `^(User\|Human\|Assistant\|System):` at line start in a `.md` | 0 | fabricated dialogue |
| `<system-reminder>`, `<function_results>`, `[Tool result]`, `hookSpecificOutput` inside prose | n/a | harness-format mimicry; superpowers quotes hook JSON legitimately in docs |
| `(inform\|notify\|tell\|let) the user .*(then\|and) (proceed\|continue\|run\|execute)` | 1 | notify-then-proceed; the one hit is benign |

## B. Definitional hijacking and defaults (class 14)

| Pattern | Base rate | Note |
|---|---|---|
| `\bmeans\b [^.]*(run\|delete\|push\|send\|post\|upload)` | 6 | redefined verbs; all six benign prose in superpowers |
| `when the user says` | (in the 6) | request mapping |
| `(by default\|defaults? to\|unless (otherwise\|told)).*(https?://\|~/\|/[a-z])` | 0 | default naming a destination |
| `if (no\|there is no) (CLAUDE\.md\|AGENTS\.md\|config)` , `is not configured` | n/a | absence-triggered default |
| `(never\|do not\|don'?t) [^.]*(except\|other than\|unless)` | 7 | safety-exception clause; all benign here |
| `\b(read-only\|idempotent\|reversible\|no side effects\|sandboxed\|harmless)\b` near a command | 38 | safety adjectives; superpowers uses "read-only" for its reviewer contract. Check each against the command body |
| `example\.(com\|org\|net)` lookalikes: `exarnple`, `examp1e`, `exampIe` | n/a | placeholder that is not a placeholder |

## C. Second-order layers (class 15)

| Pattern | Base rate | Note |
|---|---|---|
| Files named `*-prompt.md`, `*prompt*.md`, `agents/*.md`, `commands/*.md` | 5 files | subagent and agent templates; rank at or above SKILL.md |
| `allowed-tools:` , `tools:` , `model:` in frontmatter | 0 in SKILL.md | permission grant inside markdown |
| `dispatch (a\|one) subagent (per\|for each)` | n/a | fan-out |
| `(NOTE\|ATTENTION\|INSTRUCTIONS?) (TO\|FOR) (THE )?(AI\|ASSISTANT\|AGENT\|MODEL\|CLAUDE\|LLM)` | 0 | comment addressed to the model |
| Code comment lines beginning `AI:`, `Claude:`, `assistant:`, `agent:` | 0 | |
| `printf\|echo\|console\.log\|print\(` whose string contains `MUST`, a pseudo-tag, or `you ` | 2 files | scripts that emit instruction text: `hooks/session-start` (benign, by design) and one test |
| String literals in scripts containing `curl`, `http`, `run `, `install` inside an error or `exit` path | n/a | error-message instruction |
| `(include\|add\|append) (this\|the following) (footer\|line\|badge\|link\|trailer)` in generated-content instructions | n/a | second-hop boilerplate |
| `(every\|all) skills? you (write\|create) (must\|should) include` | n/a | skills that author skills |

## D. Trust elevation (class 16)

| Pattern | Base rate | Note |
|---|---|---|
| `"matcher"` values containing `compact` | 1 | re-injection after summarization; superpowers matches `startup\|clear\|compact` |
| `"PreToolUse"` with `"matcher": ".*"` or empty | 0 | every tool input visible to the hook |
| `additionalContext\|additional_context` emitted from a script | 1 | file-to-hook-to-context path |
| `<[A-Z_-]{6,}>` pseudo-tag wrappers in emitted or loaded text | present | already a class 5 locator; here it marks the elevated text |
| `read (the )?current version\|skills evolve` | present | combined with a writable plugin dir |
| `to verify[^.]*run\|verify (the )?install` | 2 | verification as execution; both benign |

## E. Environment mutation (class 17)

| Pattern | Base rate | Note |
|---|---|---|
| `ANTHROPIC_BASE_URL\|OPENAI_BASE_URL\|HTTPS?_PROXY\|ALL_PROXY\|NPM_CONFIG_REGISTRY\|PIP_INDEX_URL\|NODE_EXTRA_CA_CERTS\|SSL_CERT_FILE\|REQUESTS_CA_BUNDLE` | 0 | traffic redirection. Highest signal-to-noise pattern in this file |
| `insteadOf\|credential\.helper\|core\.hooksPath\|filter\.[^.]+\.(clean\|smudge)` | 0 | git persistence keys. Plain `git config` had 9 hits, all `user.name`/`user.email`/`gpgsign` in test setup |
| `mcp\.json\|mcpServers` | 0 | MCP registration |
| `dangerously-skip-permissions\|--yolo\|trust-all-tools\|bypassPermissions\|permissions\.allow\|allowedTools` | 0 | permission widening, either audience |
| `npm install -g\|pip install\|brew install\|npx -y\|plugin install\|marketplace add` | 0 | install by instruction |
| `~/\.claude/skills\|~/\.agents/skills\|global skills\|copy (this\|the) skill` | 20 | self-installation surface; all 20 are superpowers documenting where personal skills live. Benign, and exactly the shape a hostile "install me globally" would take |
| `MEMORY\.md\|memory/\|CLAUDE\.local\.md\|settings\.local\.json` | 0 | memory and local-settings persistence |
| `(connect\|authorize\|grant access to) (your\|the) (gmail\|slack\|github\|calendar\|drive)` | n/a | connector grant |
| `\.vscode/tasks\.json\|runOn.*folderOpen\|\.idea/` | 0 | editor auto-run |
| `export [A-Z_]+=` in prose (not in a script) | n/a | any env var set by instruction |

## F. Reader-limit evasion (class 18)

Not phrases. Measurements. Listed here so the thresholds are published.

| Measurement | superpowers | Note |
|---|---|---|
| Files with more than 2000 lines | 0 | 2000 is a common model-tool `Read` default |
| Files over 50 KB | 7 | all docs, plans, and release notes |
| Files with any line over 500 chars | 15 | longest 2005 chars (`.kimi-plugin/plugin.json`) |
| Symlinks | 0 | |
| Extension vs `file` magic mismatch | 5 `.md` reported as JavaScript | **noise**: `file` misclassifies markdown that opens with code. Record the rule and its false-positive rate |
| Non-UTF-8 or BOM-prefixed text files | 0 | |
| Archives in tree | 0 | |

## G. Human-audience and inbound surface (class 19)

| Pattern | Base rate | Note |
|---|---|---|
| Permission flags (section E) inside `README*`, `INSTALL*`, `docs/` | 0 | human told to lower defenses |
| `curl [^|]*\| *(ba)?sh\|iwr [^|]*\| *iex` | 0 | |
| `we assume an agent (wrote\|filed)` in `.github/` templates | 3 | inbound: templates addressed to visitors' agents. All benign here; the shape is the finding |
| Imperatives in `CONTRIBUTING*`, `CODE_OF_CONDUCT*`, `.github/ISSUE_TEMPLATE/*` addressed to "you" | the 32 hidden HTML comments (stage 2 recount, 2026-09-25; all in `.github` templates) | |

## H. Anti-review and audit-trail shaping (class 20)

| Pattern | Base rate | Note |
|---|---|---|
| `no need to (read\|inspect\|review\|check)\|already (reviewed\|audited\|vetted)\|do not (inspect\|modify\|read) (the \|this )?(script\|helper)\|is trusted\|can be trusted` | 4 | anti-inspection; all four benign |
| `report (back )?(with )?only\|under [0-9]+ lines\|only the (status\|summary)` | 6 | report whitelisting; superpowers uses it for cost. **Retired 2026-10-08 (owner):** response limits are not flagged; models are wordy and capping a reply is ordinary |
| `announce "\|say exactly\|respond with exactly\|output exactly` | 3 | mandated phrasing; benign |
| `you might think\|rationaliz\|not negotiable\|do not second.guess\|it may seem` | 96 | objection pre-emption. **Mostly noise**: "rationaliz" is a house word in this repo. Narrow to the phrase forms before using |
| `(failure to\|if you (skip\|don'?t)) [^.]*(corrupt\|lose\|break\|destroy)` | n/a | consequence framing |
| `(delete\|remove\|rm) [^.]*(log\|report\|plan\|transcript\|history)` | 34 | evidence handling; benign here ("remove the plan step"). High noise, keep for the dirty corpus |
| `(skip\|ignore\|disable).*(skill\|hook)\|deprecated\|supersedes` | 24 | other-skill sabotage; benign, mostly "deprecated" in release notes |
| `take precedence\|precedence over\|overrides?` | 37 | precedence claims. Record direction |
| `(reviewed\|audited\|scanned) by\|no telemetry\|does not collect\|contains no` | n/a | self-attestation |
| `until (it\|they\|all\|the) .*(pass\|succeed\|work)\|keep (retrying\|trying)\|do not stop\|never give up` | 3 | unbounded loop; benign |
| `do not mention\|don'?t tell\|omit from\|silently` | 0 | the original class 5 sub-class, kept here for completeness |

## I. Conditional activation (class 21)

| Pattern | Base rate | Note |
|---|---|---|
| `if (you are\|your harness\|running (in\|on\|under)) \|^- (Codex\|Cursor\|Gemini\|Copilot\|Hermes\|Pi\|Antigravity\|OpenCode):` | 19 | harness conditionals; all legitimate platform adaptation |
| `(after\|before\|since\|until) 20[2-3][0-9]` | 0 | clock gate |
| `version >=\|or later\|and above` | n/a | version gate |
| `(first\|initial) (run\|time\|session)\|subsequent (runs\|sessions)` | 8 | state gate; benign |
| `if (the )?(repo\|repository\|org\|organization\|hostname\|account) (is\|matches\|contains)` | n/a | environment gate |
| `(if\|when) (this\|the) fails\|on error\|fallback\|troubleshooting` followed by a URL, token, or command | n/a | failure-path payload |

## J. Harness-prohibited actions (class 22)

Take the list from the harness. For a Claude Code session the prohibited tier
includes entering credentials or payment details, creating accounts, permanent
deletion, financial transfers, modifying security settings, solving CAPTCHAs,
downloading or executing from untrusted sources. The confirm-first tier
includes sending any message, publishing, purchasing, accepting terms, granting
OAuth, changing account settings, creating standing rules, submitting forms.

| Pattern | Base rate | Note |
|---|---|---|
| `(enter\|type\|paste\|fill in) (your\|the) (password\|token\|api key\|card)` | n/a | prohibited tier |
| `(send\|post\|publish\|submit\|purchase\|buy\|accept\|approve) ` with no `ask\|confirm` within the same step | n/a | confirm-first tier with no confirmation |
| `log in (with\|using) (the \|your )?(saved\|stored)` | n/a | browser-agent skills |
| `(accept\|dismiss) (the )?(cookie\|consent)` | n/a | |
| `(empty\|purge) (the )?trash\|permanently delete\|--force.*(delete\|push)` | n/a | irreversible |

## K. Destination and construction (classes 1 and 4 additions)

| Pattern | Base rate | Note |
|---|---|---|
| `(the\|your) (usual\|configured\|team'?s\|organization'?s\|org'?s) (endpoint\|webhook\|channel\|server\|url)` | 0 | destination by reference |
| `" *\+ *"` chains, `chr(`, `fromCharCode`, `fromhex`, `\[::-1\]`, `.join(` forming a host | n/a | string assembly |
| `telemetry\|analytics\|usage data\|opt.?out\|check for updates` | 41 | consent-veneer network; here all documentation of other tools' behavior |
| Unused `^\[[^\]]+\]:\s*\S+` link definitions, `<details`, `hidden`, long `alt=` | 0 | markdown carriers |
| Fullwidth or math-alphanumeric letters in a keyword position | n/a | fold with NFKC first |

---

## L. Instruction override and takeover (class 5)

Added 2026-09-14. Fills a class-1–12 gap the coverage matrix exposed: class 5 had
no dedicated set. These are the **loud** takeover shapes — a model told, in
plain text, to drop its prior instructions or identity. Non-exhaustive by nature;
new phrasings appear constantly.

**Three cautions, non-negotiable, or this set misleads:**
1. **Run on the folded copy only.** Homoglyphs, zero-width chars, and Unicode
   tag-blocks (U+E0000–E007F) defeat every pattern here. This set is worthless
   without the reader's fold step (RED-TEAM §19, INCIDENTS).
2. **Loud only; not the discriminator.** The strongest attacks never use this
   language (RED-TEAM §2). A zero here is not safety; a hit is a locator. The real
   question stays data flow — what moves, to where.
3. **High noise; needs negatives.** Legitimate skill-authoring uses precedence and
   emphasis language (superpowers: `precedence` 37, all benign). Every family
   below needs clean-negative fixtures or it is an intensity linter.

| Family | Pattern (case-insensitive, folded text) | Base rate | Note |
|---|---|---|---|
| Ignore / disregard | `(ignore\|disregard) (all\|any\|the\|your\|previous\|prior\|above\|earlier) [^.]*(instruction\|prompt\|rule\|direction\|context)` | n/a | the canonical injection |
| Forget / reset | `(forget\|discard\|erase) (everything\|all\|what\|your\|the previous)` , `(reset\|clear\|wipe) (your\|the) (context\|memory\|instructions\|history)` , `start (over\|fresh\|anew)` | n/a | user's seed; `forget` |
| Override / supersede | `(override\|overrides?\|supersede\|supersedes\|replaces?) [^.]*(instruction\|prompt\|rule\|system\|directive\|guardrail)` , `this (message\|section\|file) (wins\|takes precedence\|is authoritative)` | n/a | user's seed `override`; narrow — bare `precedence`/`overrides` alone is class-20 noise (37 benign) |
| Identity reassignment | `(you are now\|from now on,? you\|you will now (act\|behave)\|act as\|pretend (to be\|you are)\|roleplay as\|you are no longer)` | n/a | `you are DAN`, `developer mode` variants land here |
| New / true instructions | `(here are\|these are\|the following (are\|is)) your (new\|real\|true\|actual\|updated) (instruction\|task\|rule)` , `new instructions?:` | n/a | authority reframe |
| Fabricated system framing | `^\s*(system\|<system>?\|\[system\]\|<\|im_start\|>system\|### instruction)` at line start in prose | n/a | delimiter/role injection; overlaps class 13 (fabricated dialogue) |
| Rule / guardrail suspension | `(ignore\|bypass\|disable\|turn off\|drop) (your\|all\|any) (guideline\|rule\|policy\|restriction\|safeguard\|filter\|guardrail)` , `no (restrictions\|limits\|filter)` , `\bjailbreak\b` , `\bunfiltered\b` , `do anything now` | n/a | the loudest; near-zero benign, so a hit is high-value |
| Context-end injection | `end of (system )?prompt` , `---+\s*(end\|ignore)` , `</system>` , fenced blocks claiming to close the system prompt | n/a | fake delimiter to escape context |
| Priority hijack | `(this is\|treat this as) (the )?(most important\|highest priority\|top priority\|above all)` , `IMPORTANT:? ignore` | n/a | urgency/priority reframe; overlaps class 20 precedence |

Suppression ("do not mention", "don't tell the user") is the takeover *companion*
but lives in set H (class 20). The `silently` false positive (Case 002, 48 hits)
is the standing warning for the whole set: narrow to explicit forms, always
carry the benign share.

2026-10-09: `H.suppress` also matches hiding the record of changes ("omit / leave out / hide
... what you changed / the changes"; THREATS 20 "omit from the summary"). Retiring
`H.report-only` had dropped the one recall line of this shape. Length limits stay unflagged.
Hits on the seven audited repositories: 0 (only the fixture line).

Every family's base rate is `n/a` until run against a clean corpus and validated
against a `Fixtures/04-phrases/` positive — the near-zero families (guardrail
suspension, context-end injection) are the ones to run first on an unknown repo.

---

## What the base rates say

Of 40-odd patterns run on a repository known to be clean, about half return
zero and the other half return between 1 and 96 hits, every one benign. The
high counts (`rationaliz` 96, `telemetry` 41, `safety adjectives` 38,
`precedence` 37, `evidence handling` 34) are the patterns that would generate
the noise in a naive scanner. The zeros are the patterns worth running first on
an unknown repository, because a non-zero there is rare enough to be worth a
human's time.

Precision on a dirty corpus is unknown for every row. That is the next
measurement, not this one.

---

## Stage 4 v1 measurement (2026-09-29)

First run of the built pattern engine (`stages/04-phrases/`, grader 04 PASS:
gate 31/31, negatives 46/46, recall 39/39) on the same superpowers v6.3.0 copy:
775 hits in 194 scanned text files, one hit per line per check. By audience:
403 human, 199 tool, 169 model, 4 subagent. No hit needed the fold to match.
Every hit is a locator; none has been judged.

**Why these differ from the per-row rates above.** The earlier hand counts did
not record which files they covered, and several were clearly narrower than the
whole tree. Examples: install by instruction 31 here against 0 (README's
`/plugin install`), permission flags 17 against 0 (15 in `tests/`),
`additionalContext` 32 against 1, permission flags in docs 2 against 0. Treat the
stage 4 column as the base rate from now on; it is reproducible
(`run.py <repo> --out <dir>` writes per-pattern counts, zeros included).

The check total counts lines; the pattern counts in brackets count pattern hits,
so they can sum past the total where two patterns of one check hit the same line.

| Set | Check | Earlier hand counts | Stage 4 v1 |
|---|---|---|---|
| K | `phrase.K.exfil` | telemetry 41, dest-ref 0, md-carrier 0 | 54 (telemetry 24, http-verb 23, assembly-code 3, md-carrier 3, data-flow 1) |
| (class 2) | `phrase.creds` | none | 59 (env-enum-code 33, secret-name 20, dotenv 3, enumerate 2, path 1) |
| (class 3) | `phrase.remote-load` | none | 8 lines (fetch-follow 5, branch-ref 4, raw-host 1; patterns overlap on some lines) |
| L | `phrase.L.override` | all n/a | 45 (skip-confirm 25, forget 13 of which 12 are the TDD skills' "Start over.", override 5, identity 1, guardrail 1; ignore, system-frame, context-end, priority 0) |
| A | `phrase.A.consent` | 0 on six rows, notify-proceed 1 | 18 (harness-mimicry 16, scope 1, notify-proceed 1) |
| B | `phrase.B.defs` | means 6, safety-exception 7, safety adjectives 38 | 36 (safety-adjective 22 narrowed to "near a command", means 8, safety-exception 7) |
| H | `phrase.H.anti-review` | 4, 6, 3, 96, 34, 24, 37, 3, 0 | 66 (evidence 19, sabotage 17, precedence 7 narrowed, report-only 6, mandated 5, anti-inspect 4, preempt 3 narrowed, unbounded 3, self-attest 2, suppress 1) |
| I | `phrase.I.conditional` | harness 19, clock 0, state 8 | 75 (failure-path 36, harness 26, state 8, clock 3 widened to month names, version 2, environment 1) |
| E (perms) + class 7 | `phrase.E.perms` | permission flags 0 | 113 (exec-primitive 41, install-global 26, outlives-session 25, perm-flags 17, write-then-exec 4) |
| C | `phrase.C.second-order` | emit-instruction 2 files | 18 (error-instruction 12, emit-instruction 5, boilerplate 1) |
| D | `phrase.D.trust` | compact 1, additional-context 1, verify-run 2 | 78 (pseudo-tag 40, additional-context 32, compact-matcher 2, current-version 2, verify-run 2) |
| E (env) | `phrase.E.env` | install 0, self-install 20, rest 0 | 52 (self-install 20, persist-target 16, export 11, install 5) |
| J | `phrase.J.prohibited` | all n/a | 141 (confirm-first 139, irreversible 2). Confirm-first is unpaired until stage 4 part 2 checks for a confirmation in the same step |
| G | `phrase.G.human` | agent-template 3, rest 0 | 12 (agent-template 5, contrib-imperative 3, perm-flags-docs 2, trust-grant 2) |

**Zero on this repo, so the ones to run first on an unknown repo:** relay
hosts, chat webhooks, DNS exfiltration, encode-then-send, destination by
reference, traffic-redirection variables, git persistence keys, MCP
registration, memory persistence, ignore-previous, fabricated system framing,
context-end injection, claimed prior consent, standing approval, entering
secrets, pipe-to-shell.

**Rows added beyond this file, from THREATS** (source cited per row in
`patterns.yaml`; fold them into the tables above when a set is next revised):

- Class 1: K.dest-stored, K.assembly-prose, K.telemetry-send, K.relay-host,
  K.chat-webhook, K.http-verb, K.dns, K.encode-send, K.data-flow (a private data
  source, a sending verb, and a destination on one line).
- Class 2 (no set here before): creds.path, creds.dotenv, creds.secret-name,
  creds.env-enum-code, creds.enumerate, creds.desktop, creds.recon.
- Class 3 (no set here before): RL.fetch-follow, RL.raw-host, RL.pipe-shell,
  RL.branch-ref, RL.cross-repo-skill.
- Class 5: L.skip-confirm. Class 13: A.per-settings. Class 14: B.includes-verb,
  B.def-destination.
- Class 7: E.exec-primitive, E.outlives-session, E.write-then-exec,
  E.allowlist, E.confirm-off, and E.install-global (global and plugin installs
  moved here from set E's install row, because THREATS assigns install by
  instruction to class 7; project-local `pip install` / `brew install` stay in
  set E).
- Class 15: C.guard-instruction, C.guard-routing. Class 16: D.hook-inject,
  D.authority. Class 17: E.persist-target.
- Class 19: G.launch-lowered, G.paste-terminal, G.trust-grant.
- Class 22: J.prohibited-other, J.confirm-first-other (from the harness tiers in
  set J's preamble, which had no row).

Rows added 2026-09-29 from Case 003: `C.script-instruction` (a runnable command
handed over as an instruction inside a script string, scripts only; stage 5
pairs it with a context-injecting hook), `E.harness-binary` (re-signing or
patching the host agent's own binary, under class 17). Superpowers: 0 and 0.
`C.emit-instruction`'s pseudo-tag is now uppercase-only (a `<new-version>` usage
placeholder is not a wrapper tag).

`J.confirm-first` narrowed 2026-09-29: send / post / accept / approve need an
outward object (a message, email, comment, payment, PR, channel, terms). On
superpowers the row went from 139 lines to 30 and the stage 4 rubric from 19 rows
to 8; agent-to-agent "send the batch to a subagent" no longer counts.

Rows widened from this file (each stated in its `source`): L.ignore,
L.identity, L.new-instructions, L.guardrail, A.prior-consent, B.means,
H.anti-inspect, H.report-only, H.suppress, I.clock, I.environment,
E.git-keys, E.mcp, D.additional-context, C.skills-author, G.agent-template,
G.pipe-shell, J.enter-secret. The `[^.]*` "same sentence" span is implemented as
`(?:[^.]|\.\S)*?` so it crosses the dots inside URLs and file names.

**Open, from the build:** the class 21 fixture calls "If no config file exists,
create one with default values" benign, but it is exactly class 14's
absence-default shape and B.absence records it. Both are right: it is a
locator hit on a benign line, which is what the benign count is for.

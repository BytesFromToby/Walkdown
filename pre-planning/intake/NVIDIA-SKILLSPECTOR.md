# Intake: NVIDIA/SkillSpector

2026-10-30. Read at commit `efb4e8c` (2026-10-30), Apache-2.0. Read only: no file from it was
run or imported. Paths are relative to `src/skillspector/` unless they start with `tests/`,
`docs/`, or `contrib/`.

**What it is.** A scanner for agent skills, and the closest tool to Walkdown in purpose. It has
a LangGraph pipeline: ingest, build context, 26 analyzers in parallel, an LLM meta-analyzer,
a coverage ledger, and the report. There are about 104 deterministic rule ids, 11 LLM rules,
28 YARA rules, and an MCP-registry mode. Its README claims "71 vulnerability patterns across
17 categories" (README.md:27); the code has moved past that.

**Where it differs from Walkdown.**
- It scores. Each finding gets base points by severity × confidence, with repeats discounted.
  The total is capped at 100, banded, and mapped to `SAFE` / `CAUTION` / `DO_NOT_INSTALL`
  (`nodes/report.py:95-111`, `:582-675`).
- Its meta-analyzer asks the model for intent: malicious, negligent, or benign
  (`nodes/meta_analyzer.py:155`).
- It has no rendering, no OCR, no PDF text, and no load graph: every text file is scanned
  alike.
- It reads Claude Code's settings and hooks more deeply than Walkdown does. Its supply-chain
  rows are broader. It has a few phrase families Walkdown lacks.

**Already credited.** `CREDITS.md` cites SkillSpector and an outside evaluation of it.
Anything taken below adds a line there saying what was taken. Copying rule text or fixtures
brings Apache-2.0 §4 with it: keep the license, mark the changes, and add an entry to
`THIRD-PARTY-NOTICES.md`. Two of its parts carry other terms. The YARA files are based on
Neo23x0/signature-base (DRL-1.1), and `unicode_confusables.py` comes from Unicode
`confusables.txt` (Unicode license). Do not copy either without honoring those terms.

---

## Items

Each item: what to add, the SkillSpector source, what Walkdown has today, and where it would
go. Ordered by value for effort. `[= CF-n]` marks an item that the Cloudflare intake also
raised.

### SS-1. Claude Code settings shipped in the repository

The largest gap found. A cloned repository's `.claude/settings.json` (and a committed
`settings.local.json`) applies when someone opens Claude Code in it. Walkdown reads hooks out
of these files and nothing else.

- **Source.** `nodes/analyzers/bundled_execution_surface.py`. BH3 covers permission grants
  (`:1815`, modes at `:1200`, env at `:235-247`). BH4 covers keys that run commands
  (`:1854`, key lists at `:200-224`).
- **Today.** `struct.hooks` covers the `hooks` key. `restrictions.py` knows `defaultMode` only
  as a restriction (`limit.setting`). `E.redirect-var` matches `ANTHROPIC_BASE_URL` and the
  proxy variables as text. `statusLine`, `apiKeyHelper`, `enableAllProjectMcpServers`, and
  `LD_PRELOAD` appear nowhere in `stages/`.
- **Add.** `struct.settings` in stage 1 (`configs.py`), one row per key that matters:
  - `permissions.defaultMode` (`bypassPermissions`, `acceptEdits`), `permissions.allow` (whole
    tools, `Bash(*)`, root or home paths), `additionalDirectories`.
  - `enableAllProjectMcpServers: true` and `enabledMcpjsonServers`, which switch on the
    repository's own `.mcp.json` servers without a prompt.
  - Keys that run a command: `apiKeyHelper`, `awsAuthRefresh`, `awsCredentialExport`,
    `gcpAuthRefresh`, `otelHeadersHelper`, `statusLine`, `fileSuggestion`. SkillSpector notes
    that `disableAllHooks` turns off only `statusLine` and `fileSuggestion` (`:210-224`).
  - `env` names (never values). Some change what runs: `LD_PRELOAD`,
    `DYLD_INSERT_LIBRARIES`, `NODE_OPTIONS` with `-r` / `--require`, `GIT_SSH_COMMAND`,
    `CLAUDE_CODE_SHELL_PREFIX`. Others change where traffic goes: `ANTHROPIC_BASE_URL`, the
    Bedrock and Vertex base URLs, `HTTP(S)_PROXY`.
- **Stage 5.** A command key is exec-at-load. A permission mode or broad allow is elevated. A
  traffic redirect is network, and evidence for "Can send data out". MCP auto-enable makes
  every `.mcp.json` server live at install.
- **Verify first.** Which keys Claude Code honors from *project* settings, as opposed to user
  or managed settings, changes between releases. SkillSpector marks `auto` mode "ignored by
  surface" in project settings (`:1200`). Keep the key list dated, like `hosts.yaml`, and
  check each key against the current settings docs before the report says what it does.
- **Fixture.** A `.claude/settings.json` with each key, plus a `settings.local.json`, plus a
  repository where the same keys appear only in a README. The README case must not count.

### SS-2. MCP servers and hook commands that run whatever version is current `[= CF-1]`

- **Source.** RP1 and RP3 (`nodes/analyzers/mcp_rug_pull.py:129-145`, `:502`).
- **Its weakness, to avoid.** `_VERSION_PIN_RE` (`:145`) is `@[\d.]+\b|==[\d.]+|:[\d.]+|@sha256:`.
  `@1` and `:3` count as pinned, so a major-version float passes as a pin. Walkdown should
  record `exact` (full version or digest), `range` (major-only tag, `^`, `~`, `>=`), and
  `none`.
- **Also there, and dead code.** A diff against a previous manifest
  (`mcp_rug_pull.py:554-660`) never runs, because `previous_manifest` is hard-coded to `None`
  (`nodes/build_context.py:3988`). Walkdown's version drift (`changes.md`) already does this
  job.

### SS-3. A skill or command named like a host built-in `[= CF-2]`

- **Source.** TR2 (`static_patterns_supply_chain.py:3456`, `:3562`, against
  `_BUILTIN_COMMANDS`). TR1 (a trigger of one common word, or two characters or fewer) and TR3
  (keyword baiting: `anything`, `always`, `all messages`; `:3470`) are worth a row each under
  `trig.guidance`.

### SS-4. Letters spread apart to dodge a match

- **Source.** AE6 (`artifact_integrity.py:1114`), and the "compact letter view" in
  `artifacts.security_text_views` (`:2349`), which collapses `i g n o r e`, `i-g-n-o-r-e`, and
  words split across lines. There is also a reconstruction pass (`security_reconstruction.py:1947`)
  for instructions that say how to rebuild a command: "remove 'xyz' from 'rxyzmxyz -rxyzf *'
  and execute" becomes `rm -rf *`.
- **Today.** Stage 2 folds invisible and look-alike characters, and stage 4 joins wrapped lines.
  Visible separators between single letters are not folded.
- **Add.** (a) A fold rule: a run of four or more single letters separated by one repeated
  separator (space, dot, hyphen, underscore) reads as the word. The hit carries the carrier
  `spaced`, as base64 hits say they were decoded. (b) The reconstruction case as a phrase
  shape, not a decoder: "remove / strip / delete every <x> from <string> and run / execute",
  in the K.assembly-prose family. Walkdown reports the instruction to rebuild; it does not
  rebuild the command.
- **Measure.** Spaced letters are common in benign Markdown (`A B C`, table art). Record the
  benign count on the corpus before trusting a zero.

### SS-5. Reading other agents' configuration and other installed skills

- **Source.** AS1 to AS3 (`static_patterns_agent_snooping.py:57-128`): `~/.claude`, `.codex`,
  `.gemini`, `.continue`; `mcp.json` files and `claude_desktop_config.json`; enumerating
  `~/.claude/skills/*`. Its own path is excluded (`docs/AS3_SELF_REFERENCES.md`).
- **Today.** `E.persist-target` (`patterns.yaml:626`) matches *writing* to those places.
  Nothing matches *reading* them. MCP configs often hold tokens in `env`, which makes them
  credentials.
- **Add.** A `creds.agent-config` row: a read verb with one of those paths. It is evidence for
  "Can read your data". A skill reading its own folder never counts.

### SS-6. Text that asks the model to disclose its context

- **Source.** P6 to P8 (`static_patterns_system_prompt_leakage.py:67`, `:121`, `:165`):
  "print / reveal your instructions", "repeat everything above", "write the prompt to a file".
  E4 (`static_patterns_data_exfiltration.py:125`): the conversation or context sent out.
- **Today.** None of these shapes is in `patterns.yaml`. `K.data-flow` may catch part of E4.
- **Add.** Rows under 4a with the class taken from THREATS (class 1, or a new bullet). Expect
  benign hits in prompt-engineering guides; record them.

### SS-7. Refusal and warning suppression; steering the answer

- **Source.** AR1 to AR3 (`static_patterns_anti_refusal.py:54`, `:77`, `:99`): "never refuse",
  "without warnings / disclaimers / moralizing", "developer mode enabled". P4
  (`static_patterns_prompt_injection.py:160`): "always recommend X over Y", "append this to
  every response".
- **Today.** `L.guardrail` covers "no restrictions", "jailbreak", "unfiltered", and "do anything
  now". It does not cover "never refuse", "without disclaimers", or the steering shapes.
- **Add.** Extend `L.guardrail` for refusal and warnings. Add a separate 4b row for steering
  ("always recommend / prefer <x> over / instead of"): a skill that steers recommendations
  toward one product is taking the wheel, and it is common in vendor skills. Base rate first.
- **Also from SkillSpector.** Its defensive-context filters (`static_patterns_anti_refusal.py:136-311`:
  security checklists, "example:", retrospective "the old agent would…") are worth
  reading next to `negation.py` for exception shapes Walkdown lacks.

### SS-8. Handing the work to another model or provider

- **Source.** EA5 (`static_patterns_excessive_agency.py:209-275`): frontmatter `model:` /
  `provider:` naming another vendor; `claude -p`; `codex exec`; `-m` / `--model` in shell
  fences.
- **Today.** `need.command` records that `claude`, `codex`, and `gemini` run (`tools.yaml:70-72`).
  `clean.model` records pinned model ids. Nothing joins them.
- **Add.** In stage 5, a skill that pipes text to another agent CLI or vendor API sends that
  text to another provider. That is "Can send data out" evidence. The flags it passes
  (`--dangerously-skip-permissions`, `--yolo`) already hit `E.perm-flags`, so pair them: one
  line that hands work to a second agent and lowers its permissions.

### SS-9. Compiled files that ship where the source looks clean

- **Source.** SC8 (`static_patterns_supply_chain.py:3737`, `:3751`). Their rationale:
  "Discovery skips these paths, so malicious bytecode can score SAFE while decoy sources look
  clean."
- **Today.** Stage 1 counts every shipped file. Nothing calls out `.pyc` / `__pycache__`,
  `.class`, `.wasm`, or minified JS with no matching source.
- **Add.** A `struct.census` flag, `compiled`, listed in stage 7 as unread. Pair it with
  stage 3 when a script that the skill runs has a compiled twin.

### SS-10. Text inside archives

- **Source.** `nested_artifacts.py`, `docs/NESTED_ARTIFACT_INSPECTION.md`: ZIP-family members
  are read in memory to depth 3, with limits of 1,000 members, 25 MiB, a 100:1 compression
  ratio, and 5 s. Members get virtual paths such as `a.zip!/b.zip!/x.sh`.
- **Today.** `struct.census` flags an archive. Stage 2 opens ZIPs only to identify the kind
  (`files.py:73`) and to read DOCX.
- **Add.** Stage 2 reads text members of ZIP archives under limits like those above, citing
  `archive.zip!/path`. A member that is not read goes to stage 7. Stage 3 counts an archive
  as loaded only if an instruction unpacks it. (`.skill` and `.plugin` bundles are ZIPs.)

### SS-11. Padding that pushes text out of view

- **Source.** P9 (`nodes/analyzers/whitespace_padding.py:58-65`): 20 blank lines, an 80-space
  run, files that are 90% whitespace, one character repeated 512 times, one line repeated 64
  times. MP2 (`static_patterns_memory_poisoning.py:85`): a short string repeated 20 or more
  times.
- **Today.** `struct.census` has the reader window and long lines. Padding inside the window,
  which moves text below a viewer's fold, is not flagged.
- **Add.** `struct.census` flags `pad-blank` and `pad-repeat`. Stage 5 pairs a pad with a
  phrase hit after it.

### SS-12. Small rows for the phrase table and the endpoint census

Each needs a source line in THREATS or PHRASES before it goes into `patterns.yaml`.
- **Special addresses** in `endpoint.host`: cloud metadata (`169.254.169.254`,
  `metadata.google.internal`, `100.100.100.200`, `fd00:ec2::254`), loopback, and private
  ranges, marked by kind (SSRF1 and SSRF2, `static_patterns_ssrf.py:39`, `:54`).
- **Container escape and the host socket.** `/var/run/docker.sock`, `--privileged`, `-v /:`,
  `--pid=host`, `nsenter`, Kubernetes `privileged: true` / `hostPath` (PE4, PE5, TM4). These go
  under `phrase.E.perms` as elevated.
- **Certificate checks off.** `verify=False`, `NODE_TLS_REJECT_UNAUTHORIZED=0`, `curl -k`,
  `--no-check-certificate`, `--disable-content-trust` (TM3, SC7). Evidence that traffic can
  be read in transit. Count it in scripts the skill runs as well as in instructions.
- **Package registry redirected in a config file.** `.npmrc` `registry=`, `pip.conf`
  `index-url`, `.cargo/config.toml`, a Poetry or Maven source, including ones written by a
  heredoc (SC10, `dependency_sources.py`, `docs/DEPENDENCY_SOURCE_REDIRECTION.md`). Today
  `E.redirect-var` catches only the environment-variable forms.

### SS-13. Never honor a suppression the audited repository ships

- **Source.** `suppression.py`, `docs/SUPPRESSION.md`. A baseline shipped inside the scanned
  skill is ignored unless the user passes `--use-shipped-baseline` (`cli.py:544`), because
  the author could otherwise hide findings.
- **Walkdown.** Marks live in the run folder, not the audited tree, so this probably holds
  already. Make it a written rule in `stages/CONTRACT.md` with a test: a `marks.json`,
  `.walkdown*`, or `baserates.json` placed in the audited repository changes nothing.

### SS-14. A coverage gap as a result `[≈ CF-3]`

- **Source.**
  - AE1: a referenced file not fully read (`nodes/finalize_inspection_ledger.py:647`).
  - AE5: a file too large for a whole-file model read (`artifact_integrity.py:1051`).
  - AE7: the tail of a file past the cap was not read (`:692`).
  - Unsupported primary content is fatal: a UTF-16 `SKILL.md`, a TAR
    (`docs/scan-completeness.md`).
  - `--fail-on-incomplete` and `--min-coverage` (`cli.py:586-600`).
- **Add.** Fold this into the CF-3 ledger. One specific row to add: a reference whose target
  could not be read is listed in stage 7 next to the line that referenced it.
- **Owner's call.** An exit code for an incomplete *run* says nothing about the repository.
  It would let CI notice a run that went blind. Whether that fits the no-verdict rule is the
  owner's decision.

### SS-15. Stage 6 hardening, compared

- **Their Claude CLI flags** (`providers/_agent_cli.py:195-290`): `--allowed-tools ""
  --tools "" --permission-mode dontAsk --strict-mcp-config --setting-sources=
  --disable-slash-commands --system-prompt … --no-session-persistence`. The prompt goes in on
  stdin, and the command runs from an empty temp directory.
- **Walkdown's** (`stages/06-soft/back_claude.py:38-41`) already has `--tools ""`,
  `--strict-mcp-config`, `--no-session-persistence`, `--safe-mode`, `--setting-sources ""`,
  stdin, and an empty working directory.
- **Candidates.** `--disable-slash-commands` and `--permission-mode dontAsk`, after checking
  that they exist in the current CLI and change something with `--tools ""`.
- **They refuse codex CLI** because its read-only sandbox still reads host files
  (`_agent_cli.py:319`). Apply the same test to any agent CLI added as a stage 6 backend.
- **Prompt framing.** Walkdown puts the audited text in a JSON string inside a ```` ```json ````
  fence (`back_claude.py:44-48`, `:104-106`). JSON escapes quotes but leaves backticks alone,
  so a quoted line holding ```` ``` ```` can appear to close the fence. SkillSpector has the
  same weakness in a plain fence (`llm_analyzer_base.py:974`). The fix is a random
  per-request delimiter, or escaping backticks in the JSON.
- **Output checks.** SkillSpector passes a rule id the model supplies straight through
  (`llm_analyzer_base.py:684`). Walkdown checks labels against the option list
  (`back_claude.py:122`, `back_jev.py:149`). Keep it that way, and record malformed answers
  as skipped, never as empty.

### SS-16. Its fixtures as known positives someone else wrote

- **Source.** `tests/fixtures/`, Apache-2.0: `malicious_skill`, `mcp_poisoned_tool`,
  `mcp_overprivileged`, `mcp_underdeclared`, `mcp_mismatched`, the `ssd*` / `sdi*` / `sqp*`
  positive and clean sets, `pe3_bare_keyring`, `as3_self_reference`.
- **Why.** MODEL-ACCURACY notes that the sweep's test set "was written by the same person who
  wrote the question". These were not. Running the sweep and stage 4 on them is a check from
  outside.
- **How.** Copy them into `Fixtures/` under a dated folder, keep the license, and mark them as
  changed if they are changed. The owner writes the ANSWERS sheet. The blind-build rule
  holds, since no detector is built from them.

### SS-17. Run it beside Walkdown on calibration audits

As the Cisco skill-scanner was run. Record where the two disagree, by class. Use `--no-llm`
for the deterministic comparison. Run it in a sandbox, because it is third-party code.

---

## Lessons from `contrib/batch_scan/docs` that apply to Walkdown

- **English-only rules go blind on non-English text.** `DESIGN.md:135` counts 25 rules that
  lose recall, 8 of them with no fallback. Their language check is a script ratio that
  misreads Japanese with many kanji as Chinese, and sends Cyrillic, Arabic, and Devanagari to
  "en". Walkdown's `read.script` + `read.language` is ahead; this is a known failure to test
  against.
- **Check model output in layers:** JSON, then schema, then confidence, then the label
  allowlist. Keep "bad JSON" apart from "the schema changed" (PITFALLS, "Narrow exception
  handlers"; BUGS B8).
- **Instrumentation can look wired up and not be.** A `from x import f` copy escaped their
  patching, and 95% of LLM calls bypassed the key pool (B16). Test the path that actually
  runs.
- **A hung worker should not cost the report.** Record a timeout row and keep going (B9).
  Without checkpoints, a crash late in a batch loses the whole batch (FUTURE_WORK §2). This
  matters for stage 6 on large repositories.
- **Always test the real model path before calling it done.** Their `--no-llm` runs hid most
  failures.

## Where Walkdown is ahead (keep)

- What a person sees against what the model receives: rendering, OCR, PDF pages, hidden
  carriers. SkillSpector matches HTML comments by regex and has none of the rest.
- A load graph with depth, dynamic loads, orphans, and unlisted components. SkillSpector
  scans every file alike and follows only up to 256 references (`references.py`).
- `AGENTS.md`, `CLAUDE.md`, `commands/`, and `agents/`, which SkillSpector does not model.
- Version drift that runs. Theirs is dead code.
- Fit against grants per skill. Their LP1 to LP4 do this per repository, from the code only.

**The no-score rule, from their own code.** `_max_issue_severity` (`nodes/report.py:533`) exists
because, in the code's words, the normalized band "can read LOW while issues[] contains a HIGH
finding". It is a working example of why Walkdown adds nothing up. Cite it in the charter's
reasoning if useful.

## Not taken

- **The risk score, bands, `DO_NOT_INSTALL`, SARIF severities, and the score floors.** No
  score, by rule.
- **The meta-analyzer's intent field** (malicious, negligent, benign). It reports intent,
  where Walkdown reports capability.
- **P5 harmful content** (poison recipes and the like). This is content policy, not what
  installing grants.
- **OSV lookups, abandoned-package and typosquat lists, YARA malware rules, Python AST and
  taint, and deserialization rows.** This is conventional code tooling, which the charter
  leaves to existing scanners, and the YARA rules carry DRL-1.1. One narrow version may be
  worth it later: AST checks on scripts that a hook or a skill runs, since those reach the
  model's context.
- **`--transitive` fetching of external references.** Walkdown names an outside reference and
  never opens it (CF-5 turns that into a stage 7 row).

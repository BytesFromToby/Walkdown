# Changelog

Each version lists what a user would notice. The version is in `VERSION`, printed by
`python walkdown.py --version`, and recorded in every run's LOG.md with the git commit
("+modified" when the code had uncommitted changes).

## Unreleased

- **Every report says what Walkdown examined, in three colours.** Walkdown will not read every kind of file, so the
  summary, `details.html`, `full.md`, and the brief now sort the files by type: white for what the checks read (text,
  and PDFs, Word documents, and images the reader drew text out of), yellow for archives (looked inside for programs
  only), and red, "No tests are run on these file types", for everything else, with how many of them the AI loads.
  `details.html` names the yellow and red files, and `full.md` every one with why. "Unknown file type" is gone from
  "Files worth a look" (its files are red), and the archive row there says what was checked. The brief's first line
  says `Files: <n>`, and its second how many were examined. "What Walkdown didn't check" no longer counts those files
  again ("N files could not be read", and the phrase step's "not text" files); one line points to the colours instead.
- **Descriptions in an MCP server's code are read as text the model reads.** A client sends each tool's, prompt's, resource's,
  and parameter's description to the model as it stands, but Walkdown read an MCP server's Python, JavaScript, or Go as code only, so
  an instruction hidden in a tool's docstring or a parameter's description counted as "not in text a model reads". In a file
  that imports an MCP library, those strings are now scanned again as model text, and a hit there counts as in text a model
  reads (`tool_text` on the finding). The same goes for what a server's prompts return and the text of its tools' replies (error
  messages included), which the model also reads. Measured on the official servers, the Python SDK, fastmcp, and GitHub's Go server;
  a client's arguments to a server are left out. Its review card and `details.html` say why: "This line is code, but an MCP server
  sends these words to the AI: ... So the AI reads them." `full.md` says `(model, sent to the AI by an MCP server)`. A server
  written in another language (Rust, Java, C#, and others) is read as code only, and every run's limits now say so.
- **What Walkdown says about a line is its own line on the review card.** What hidden characters spell and what base64 decodes to
  were put in front of the place's note, so a card read "How often this pattern turns up elsewhere: Decoded from base64: ...". They
  are a line of their own now, before the note, and `details.html` shows them for every place.
- **Asking the model for its own instructions is a pattern** (`K.prompt-leak`, 131 in all): "print your system prompt",
  "repeat everything above", "your instructions verbatim". From SkillSpector's P6 to P8, measured and narrowed first.
- **Padding and compiled programs are files worth a look.** `details.html` now lists files the AI reads where 20 blank lines or
  80 blank characters push text out of view, programs in compiled form (by their bytes), compiled Python (`.pyc`), and
  archives or documents that hold a program, compiled Python, or Office macros (zip containers; tar archives plain or
  compressed with gzip, bzip2, xz, or zstd; and 7z and RAR archives, read up to 64 MB unpacked). From SkillSpector's P9, SC8,
  and SC9. A 7z or RAR is read from its own headers, so its members' names always count; a member's first bytes are read where
  Python can unpack them (not RAR's own compression, BCJ2, PPMd, or encrypted members), and an archive with encrypted headers
  is still listed as one whose contents were not read. zstd needs `zstandard`, now in `requirements.txt`: run
  `pip install -r requirements.txt` again, or the front door stops the run and names it.
- **Five new patterns** (130 in all), from rules in NVIDIA's SkillSpector: telling the model never to refuse (`L.never-refuse`),
  to leave out disclaimers or ethical commentary (`L.no-disclaimer`), decoding hidden code and running it at once
  (`E.decode-exec`), turning off certificate checks (`E.tls-off`), and pointing a package manager at another source
  (`E.registry-config`). Each was measured on nine repositories first and narrowed where it caught ordinary prose or code.
  The never-refuse, no-disclaimer, and decode-and-run rows, and the prompt-extraction row, are places on `review.html` and count on
  the summary (decoding code and running it as runs code); the certificate and package-source rows, which ordinary repositories
  hit, are in `full.md` only.
- **No line of a private key reaches a report.** The secret scan flags a private key's first line, and the mask covered only
  that line. Hidden characters on a later line of the key's body made the reader quote that line, and `full.md` and
  `data/02.2-reader.json` printed it whole. The scan now records where the key ends (`key_end` on its `secret.found` row), and
  every line through that one is masked, the `-----END` line included. A model read already left the whole key out, and now uses
  the same lines. Counts, findings, and page wording are the same; a quote on a key's later line reads as masked, so a mark on
  such a place does not carry over.
- **A key beside readable base64 is a key.** A line holding an instruction hidden in base64 was marked as holding no key, whatever
  else the scanner flagged on it, so a hex key or base64 of random bytes on the same line was shown in `full.md` and `data/`, and
  such a skill could read "found none of the security concerns it looks for". The mark now needs every flagged value on the line to
  decode to readable text. Such a line counts as looks like a committed secret and its quote is masked; the decoded instruction
  still shows beside it, since a flagged key never decodes to readable text.
- **`.svg`, `.css`, and `.map` files are scanned for keys.** detect-secrets left them out by their extension, as it does a path
  holding `swagger`, and the pages named each as a file the scan could not scan. They are text, so the scan reads them now. Embedded
  images and source maps flag nothing in the cases checked.
- **Two hidden lines in one file keep their own marks.** A line hidden because it may hold a secret shows the same words as every
  other such line, and the mark of a place was filed under its words, so two such places with the same headline in one file shared
  one mark: on loading a saved `marks.json`, or on the next run, both marks went to the first place and the other was lost. Such a
  place is now filed under where it is. A mark saved on one before this does not carry over.
- **A key inside readable base64 is found.** The scan read a line as written, so a key that base64 on the line spelled was flagged
  nowhere, and the decoded instruction Walkdown shows put it in `full.md`, `review.html`, and `data/`. The decoded text is scanned
  too: such a key is listed at the line, with "(in text decoded from base64)" after its kind, and the decoded text is hidden with
  the line.

## 0.4.0 (2026-11-02)

The pages say what they said in 0.3.1 about the same repository, in the same order, except where
this entry lists a change. What changed is how a run is organized and named, which model reads
exist, and a few sentences. A run made by an earlier version is not read by this one, which is why
the version number moves.

### For someone using Walkdown

- **Steps have numbers and names.** 0.3.1 numbered eight stages. This version runs `01-intake`;
  the coded steps `02.1-inventory`, `02.2-reader`, `02.3-graph`, `02.4-phrases`,
  `02.5-capability`, and `02.6-builder`; the optional `03-sweep` and `04-pinpoint`; `05-qa`, the
  check of the run (below); and `06-report`. The sections of `full.md` keep their numbers and headings (1 "What ships" to 7 "Not
  examined"). The pages and the brief name a step by its plain name ("What the text asks for").
- **Intake is a step of its own.** Getting the copy (a folder, a URL cloned or updated, a GitHub
  folder link) has its own row and validation stamp in `LOG.md`. Nothing about how a URL is
  cloned changed.
- **The builder checks are a step of their own** (`02.6-builder`: needs, hosts, triggering, what the
  tools ask for, current and clean, fit, cost). Their findings are the same; a failed one is named
  "Builder checks" on the pages and in the brief.
- **The run folder.** The brief is saved as `brief.md`. `data/run.json` is the run's record, and
  `LOG.md` is written from it. `data/limits.md` replaces `data/07-limits.md`. Step files are named
  for their step (`data/02.4-phrases.json`). There is one layout: the layout of runs made before
  2026-10-02 is no longer read. A default run no longer writes the question packet
  (`data/03-packet.md`, `data/packet.json`, `data/answers.jsonl`) or a row for it.
- **Model reads.** Two exist: `--sweep jev`, then `--pinpoint claude-cli` (only after a sweep).
  Each writes exactly what it will show the model (`data/03-sweep.input.jsonl`,
  `data/04-pinpoint.input.jsonl`) before anything is sent, and keeps every answer. A run that
  chooses neither says so in one line in section 6 of `full.md`. A step with no fixtures (the
  pinpoint) shows "no fixture set" in `LOG.md`, which is not a failure.
- **A model call that gets no answer is tried again, and logged.** If a model read gets an error, an
  answer that is not one of the options, or an answer it cannot read, it waits 2 seconds and asks once
  more; if the second try answers, that answer is used. A passage that still has no answer is skipped,
  and `data/03-sweep.calls.jsonl` or `data/04-pinpoint.calls.jsonl` has one line for it (no key, no
  passage text, and no error message; only the kind of failure and a status such as 429). Section 7 and the details page say how many passages got no
  answer, with the reasons by kind, and the summary says it for a read that answered some. A key the service rejects
  twice stops the later calls. A read in which no passage got an
  answer is named as a step that did not work, and the headline says the coded checks are complete and
  the model read did not work (a model read never adds a security concern, so it does not say Walkdown
  cannot say). The pinpoint does not run after a sweep that got no answers. The check of the run (below) holds a
  run in which a read got no answer for any passage.
- **A check of the run before the report.** A new step, `05-qa`, looks at the saved run before the report
  is written and asks whether everything that should have run is there with its results. It names four
  kinds of gap: a step that did not run or failed (a model read you chose counts, when a step before it
  crashed), a step that ran and did not pass its fixture check (`FAIL`), a step whose fixture check could
  not be made (`ERROR`, `SETUP ERROR`, `NOT BUILT`, or `no fixture set` for any step but the pinpoint,
  which has no fixtures; a missing fixtures folder reads so), since the "found none" of such a step cannot
  be trusted, and a chosen model read in which no passage got an answer. With any gap the run is held: no
  report is written, the exit code is 1, and the brief says what is missing and gives two ways on. After
  a crash the brief counts what followed from it (`found 4 gaps (1 step failed, and the 3 after it did not
  start)`), a check that could not be made ends with `To see why: python tools/grader/grader.py all` (where that file
  is missing it says `tools/grader/grader.py is missing: get a fresh copy of Walkdown.`), and a
  run that also stopped as asked says so. A step with no fixtures to check against (`NOT BUILT`, `no fixture set`)
  reads `has no fixtures to be checked against`; `ERROR` and `SETUP ERROR` keep `could not be checked against its
  fixtures: it gave ...`. After `continue`, steps that ran and could not be checked are said once on the pages and in
  the brief (`8 steps could not be checked against their fixtures, so a "none" from them is not measured.`), and a run in
  which every step ran no longer says that not every step worked. A saved output that cannot be read reads `its saved
  output cannot be read`, with no "has no output" before it. `python walkdown.py continue <run folder>`
  writes the report with what ran, and the pages name every gap as a step that did not work and in
  section 7 (in the brief's words); or fix the cause (a missing key, say) and audit the repository again.
  If the report cannot be written, the run is held again, as it was; `continue` takes no `--revalidate`,
  as it takes no model option and no `--until`. A check skipped for a
  missing optional tool, the steps a stop left out, and a model read that answered some passages do not
  hold a run: section 7 names them and the run goes on. A model read that finds no key now exits 1 where it
  exited 0, because its "found none" was never a read. The check runs on every run, a stopped one
  included, and on `continue`. Section 7, `data/limits.md`, and the lists of steps that did not work are
  drawn from the check's output, `data/05-qa.json`; their words are the same for the same run. The brief of a
  held run holds no text from the audited repository.
- **Every check says what it looked at, and the run is held when one did not look at everything.** Each step from
  `02.1-inventory` to `04-pinpoint` now records, for every check it makes (or the checks that run in one pass over the
  same files), how many items it was to look at, how many it handled, how many it did not look at and says why (a
  skipped file, an unread file, a file not scanned), and how many it found. The check of the run holds a run in
  which a check looked at fewer items than it should have and does not say why, such as `The check
  "phrase.remote-load" of the step "What the text asks for" looked at 3 of 5 files; 2 are not explained.` It holds a run
  in which a check has no line at all, and one in which the counts add up to more than there were. A check skipped
  for a missing optional tool explains its items by the skip it already writes, so it is no gap, and a model read in
  which no passage got an answer has its own gap and no second one. Where a check found nothing, section 7 and the last
  section of `details.html` now say how much it looked at (`What the text asks for: phrase.K.exfil, phrase.creds and 19
  more checked 83 files, found none.`). The pages are the same otherwise. The counts are checked harder: a line's `found` is the
  results among the findings (a model read's is its flags), a line that names a check the step does not make or names one twice is a
  gap, and so is a finding whose check no line covers. What a check that found nothing looked at is its own kind of finding,
  `qa.checked`, so the limits are what they were; `full.md` has a heading for it at the end of section 7 (`Checks that found
  nothing`), `details.html` a fold after the limits (counts, no check ids, a line for each step), and a step gets it only when its fixture
  check passed, or passed with a check skipped for a missing tool, and asked at least one row. A line counts the items its checks
  read and a pass whose checks handle other items than their neighbours is a line of its own (54 lines in all, the model reads
  included). A program use is said "program use". Comparing two runs, `data/limits.md` is compared like the old `07-limits.md`. The saved output `data/02.2-reader.json` calls
  what it called `coverage` `reading` now (the name `coverage` is the list of lines); `terms.code` of the phrase
  step moves, since its scripts changed.
- **A read runs on the model you name, and says what it used.** A model option is a backend and, after a colon, a model:
  `--sweep jev`, `--sweep claude-cli`, `--sweep claude-cli:<model>`, `--pinpoint claude-cli:<model>`. The text before the first
  colon is the backend (in any case); the rest is the model exactly as you typed it. Walkdown picks no model for a run where you
  named nothing (nothing is sent), lists no models, and asks nothing; a `claude-cli` with no model named runs `sonnet`, or the model
  `WALKDOWN_SOFT_CLAUDE_MODEL` names. `claude-cli` can now do the sweep's read (it ran the pinpoint only). Refused before
  anything runs, with one sentence that says why: a model name with any character but ASCII letters, digits, and `. _ : / @ + - [ ]`
  (so no shell character, no white space, nothing outside ASCII), with `//` in it, over 200 characters, nothing after the colon, or a leading dash; `jev:<anything>` (Jev takes no model); `--pinpoint jev` (Jev answers from fixed options, and the pinpoint
  needs a line and a sentence); and a backend that does not exist. A model that takes text is shown the sweep's question, the kinds
  with their descriptions and examples, and the passage marked as data it must not obey, and answers with the name of one kind and
  nothing else; any other answer is a call with no answer. No model is asked how sure it is (Claude rated itself 0.9 or more 27 times
  and was right 12), so such a read has no probability: a passage is flagged when the answer is not `none`, and the pages say
  "(this model gives no probability)" where Jev's number would be. The pinpoint reads a flagged passage of such a read when no
  pattern covers it. **Tokens:** each model step's saved report has a `usage` block (`input`, `output`, `cache_write`, `cache_read`, and
  `calls`; a count the backend did not report is absent, never 0), the brief and section 6 of `full.md` name them
  (`Model reads used: Sweep 596,200 in, 31,464 out; Pinpoint 1,490 in, 73 out; Sweep's fixture check 39,823 in.`; "not reported"
  where a backend gave none; "(from 5 of 9 calls)" after a total that only some of the calls reported; a fixture check reused from
  an earlier run spent none and is not named), and the brief says what the
  sweep found in its own fixtures (`Sweep on jev: found 33 of 34 in its fixtures.`; a low count shows and holds nothing). A long
  read writes a plain line on the terminal every 25 passages. The sweep's fixtures have two more rows, passages that speak to the
  model reading them (one tells it to answer `none`, one tells it to use a tool). The fixture check of a model is cached by the
  model you typed, and is not kept when it measured nothing (a read that got no answer for every fixture row, with no login or no key). A saved `usage` that is not whole numbers makes the file a report that cannot be read, which the check of the run
  names as a gap. `back_claude.py` moved to `stages/_shared/` and the calls every backend makes alike (the first call alone, the one
  extra try, the stop on a rejected key, the workers) are written once in `textmodel.py`. The default pages are the same.
- **`--reads` asks for the model reads without naming a backend.** `python walkdown.py <repo> --reads claude-opus-5-5` runs the sweep
  on Jev when Jev is available (its key can be read and its package is found; the check sends nothing and shows no key), and then
  the sweep's passages go to TypeSafe, a second remote service, in place of the Claude model; otherwise the sweep runs on the Claude
  model. The pinpoint runs on the Claude model. The Claude model is the Claude Code command, run with the model exactly as typed and with
  its tools off; a bare `--reads` names `WALKDOWN_SOFT_CLAUDE_MODEL`, else `sonnet`. With Jev and `claude`: the sweep on Jev and the pinpoint on `claude`. With Jev alone:
  the sweep on Jev, the pinpoint does not run, and one note says so (`--reads: Pinpoint needs the claude command, which was not found, so it
  does not run.`). With `claude` alone: both on `claude`. With neither: refused before anything runs (`--reads: no model read can run
  here: Jev has no key or package, and no claude command was found.`). It is resolved once, before the run starts, into `--sweep` and
  `--pinpoint`: the record, the stamps, `continue`, and the pages know only those, and a run made with `--reads` is the run the same
  options make. It cannot be given with `--sweep` or `--pinpoint`, which stay for naming exactly what runs. The model goes through the
  same rule as any model name. It chooses nothing unless it is given (there is no variable for it), `WALKDOWN_SOFT_SWEEP` and
  `WALKDOWN_SOFT_PINPOINT` choose nothing beside it, and `walkdown.py continue <run folder> --reads [model]` chooses only the reads that
  can still run. `walkdown.py --reads <repo>` reads the repository as the model, and ends with one sentence that says so (exit 2).
  A value that names a backend (`--reads jev`, `--reads claude-cli:opus`) is refused: `--reads` takes a model name. The skill asks for
  `--reads` with its own exact model ID, only when the user asks for model reads, and tells the user before the run that the text goes to the model that will run,
  and that the sweep's passages go to TypeSafe's Jev instead if it is available, and runs it only on a yes. Default runs are unchanged.
- **A step that crashed is named by its error's type.** `LOG.md`, `data/run.json`, and the line printed on
  the terminal say `exit 1: ValueError`, no longer the last 500 characters of the step's messages, which
  could repeat text from the repository or a model's words. The type is read from the line that ends the
  step's last traceback and is given only when it is one of Python's own, and a missing import names its
  module only when it is one of Walkdown's packages. The whole messages stay in
  `data/<step>.notes.txt`, and nothing else a crashed step printed is read as a note, a limit, or a line of a page.
- **A file name from the repository cannot pass for a note of Walkdown's.** A step's notes often name a file of the
  repository, and a file name can hold a line break. Every note a step writes, the reader's warning that names a
  file, the bullets of `changes.md`, and the file names in section 7 and the limits now print on one line, and a
  note is a line that starts with `note: ` in its first column and nothing else. A file named with a line break and
  `note: ` in it is part of one line of the report and was never a note a step wrote.
- **A value from the repository cannot start a line of `full.md`.** A hook's matcher, a plugin's name, a front matter
  field, or a file name can hold a line break, and the rest of the value used to start a line of its own that read as
  the report's. It stays inside the row of its finding now. A value with no line break prints as it did.
- **A model read left out at `continue` is said.** Choosing a read at `continue` is the consent to send, so a
  `continue` that does not choose a read an earlier command chose does not run it. That used to pass without a word.
  Now the brief of the stop names the reads that wait (`Chosen and waiting: "Needs a human read" (jev).`) and
  prints the command with their options (`To go on: python walkdown.py continue <run folder> --sweep jev`), and
  `continue` prints a note for each read it leaves out (`note: "Needs a human read" was chosen by an earlier
  command and is not run here; --sweep jev at continue chooses it`, or, once the run has finished and `continue`
  would refuse, `to read it, audit the repository again with --sweep jev`). The run's record keeps the read (`dropped`, and the
  backend chosen), and `LOG.md`, section 6, the brief, and section 7 say it. Section 7 lists it as a limit; it is
  no gap, because the person went on without it. A read chosen again at `continue`, one that already ran, and
  one held back because the read before it got no answer are not left out.
- **A saved output that is not a report cannot trap a held run.** A step's output cut off by a full disk, or saved as
  `[]` or `{}`, or with a number or an empty object among its findings, is a gap in the check of the run, and `continue`
  writes the report with what the run has. The check, the report stage, `walkdown.py diff`, and the runner read a
  saved output by one test, so an output is a report to all of them or to none. The capability step writes
  `capability.json` whole or not at all, and a half-written one is read as none.
- **A `continue` that is killed leaves a run the same command releases.** The record says a held run is released
  only once its report is written, so a command killed in the middle leaves the run held, and running `continue`
  again finishes it.
- **Stop after a step, and go on later.** `--until <step>` stops a run after any step, so you can check
  it before it goes on: after getting the copy ("is this the copy I meant?"), after the coded findings, or
  just before a model read sends text out. Name a step by its name (`02.4-phrases`), its number
  (`02.4`), or its word (`phrases`); `coded` means the last of the coded steps. The pages and the brief
  say the run stopped as you asked and which steps did not run, and a stopped run is never counted as a run
  where a step failed. `walkdown.py continue <run folder>` goes on in the same folder. Before a model read,
  `--sweep jev --until coded` writes `data/03-sweep.input.jsonl`, exactly what the sweep would send, and
  stops without reading a key or sending anything; you open the file, and `continue --sweep jev` goes on.
  Choosing the model read at `continue` is the consent to send, and only its option chooses there:
  `WALKDOWN_SOFT_SWEEP` and `WALKDOWN_SOFT_PINPOINT` are not read at `continue` (a note says so when one is
  set), though they still choose for a first command. `continue` refuses, in one line and without touching
  the folder, when the audited folder changed since the stop, when another Walkdown stopped the run (another
  version, or the same version with other code), or when the run folder lost a step's output.
  A relative run folder works from any working folder. A run stopped before its last coded step is not
  compared with other runs.
- **Parked options are refused.** `--label`, `--compare`, `--relational`, and `--both` are not in
  this version, and neither are their environment variables: Walkdown stops at once with "not
  available in this version: labeling is being rebuilt". The Laya backend is gone. An option set to
  an off value (`--sweep none`) asks for nothing.
- **Cut.** The conditionals table (`cond.branch`) and its listing in `full.md` are gone. With the
  labels gone, section 4 says the benign share is not measured, and the cards no longer carry
  "questioned by a model" notes.
- **Words on the pages.** Sentences that named a stage by number name it by its plain name. The
  standing limit about model reads says what the sweep and the pinpoint are. The guarded actions
  (deleting, sending, paying) are described as what AI tools commonly leave to the user or ask about
  first, with no claim about one product's rules. The brief's last report line reads "Everything
  behind each answer", which describes `details.html`. A count of one reads "1 new phrase hit".
- **A fixture check that failed is measured again.** The stamp cache keeps a pass, a skipped check, and
  `no fixture set`, and no longer a `FAIL`, so a check that failed once for a reason outside the code (the
  grader was killed) no longer holds every later run of the same code.
- **`continue` takes out the pages of the stop first.** A run that stopped and is gone on with loses its
  pages, brief, limits file, and the check's output before any step runs, so a check that crashes in the
  middle leaves no page that reads as the finished run's. `marks.json` stays, and so does a page or note of your own
  beside the run: only the files the report stage writes are taken out.
- **The phrase step's version moved.** The phrase step's version (`terms.code`) moved with this version, so the first
  comparison of a run made now with one made before it says the phrase matching changed.
- **A model read does not send a line the secret scan flagged.** `--sweep`, `--pinpoint`, and `--reads` sent a flagged key to the
  service chosen, and kept it in the read's input and answers files. Such a line now goes as a blank at its place, with the rest of a
  private key, so the model does not read what else stands on it. A passage with nothing else in it is not sent, and neither is a file
  the scan did not read. `details.html` and section 7 of `full.md` say how many lines were left out and name each such file.
- **A key repeated in a file is flagged on every line.** The secret scan named only the first line of a key that appears twice in
  a file, and only the first GitHub token of a file however many different ones it held, so a later line kept its quote and its key
  on the pages and in `data/`. Each such line is now counted and its quotes are masked, which can raise the count under "Passwords
  and keys".
- **A key in hidden text is masked too.** A key the secret scan flagged was still printed in `full.md`, and kept in
  `data/02.2-reader.json`, when it sat in hidden text: on a line with hidden characters, in a hidden comment, or on a
  later line of hidden text that started above it (an HTML comment, a collapsed section, a `display:none` block, an SVG
  title). That text now reads `[line not shown: it holds what looks like a secret; open the file to see it]`, as a
  phrase hit on such a line already did, and every hidden place is still counted and named by file and line.
  The saved reader file is masked right after `02.5-capability`, the last step that reads its hidden words, so a run
  stopped before that step holds them there until it goes on. A re-render masks what it reads and writes no step output.
  A mark saved on such a hidden place does not carry over. `normalized/` still holds each file's own text.
- **A key the scan flagged is masked in every field of every step.** It could still reach `full.md`, `details.html`, even
  `summary.html`, and `data/`, from a skill or agent description (on any line of a block), a tools list, a hook's command, matcher, or event, an
  MCP server's name, command, or address, a manifest, a license field, a reference to a missing file, a folder pattern, a web address,
  a repeated sentence, a conflicting definition, a tool setting, a frontmatter name, key, or value, a model ID, or a package name. Each now reads
  `[line not shown: it holds what looks like a secret; open the file to see it]`. Every place is still counted and named. A plain event or
  tool name stays (`SessionStart`, `Read`), and a hook whose command is masked is named by its line (`hooks/hooks.json:4`). A host goes only
  when every place naming it is flagged. Each saved step output is masked once the last step that reads its words has run (`02.6-builder`,
  or a step that failed), so a run stopped earlier holds them there until it goes on. `changes.md` shows no word from a file
  masked in either run. A mark saved on a masked hook does not carry over.
- **Old runs.** A run made before 0.4.0 is not re-rendered, and a new run does not compare itself
  with it: the new run, `changes.md`, and the brief say the earlier one is not comparable, in one
  plain line. Audit the repository again to get a run in the current form.
- **Marks carry over.** A `marks.json` saved before 0.4.0, and the marks of an earlier run, still
  load. A place now has two keys in `review.html` (one from the step's name, one the old way), and
  either finds your mark. Nothing is rewritten in your file.
- **Previous run.** One rule finds "the previous run": the newest other run of the same repository
  that finished before this one started. Two runs on one day are ordered correctly.
- **Fixes.** `--fresh` works on Windows (it could not delete the read-only files git leaves in a
  clone). A GitHub folder link whose folder path holds `..` is refused before anything is cloned.
  When intake refuses a target, the terminal shows its one error line and no second one. In the
  brief, an earlier run that cannot be compared is no longer called "(version drift)". `LOG.md`
  says "1 finding", and one new phrase hit reads "1 new phrase hit (in text a model reads)". The
  test-data limit and the not-comparable page read correctly; the page names the version to audit
  with.
- **What counts as "Walkdown changed".** An edit to a comment or a docstring in the phrase step's
  code, or to a word list's `source` label, no longer reads as a change to the matching code or the
  word lists. Both recorded values change once with this version. The list of invisible characters
  counts as part of the matching code, since a keyword split by a listed character matches because
  of it: a change to the list reads as "matching code changed". So does a change to the shared code
  that decides a hit (the text reader, the audience rule, the secret mask, and the helper that reads hidden
  characters). A change to the plumbing the phrase step imports does not: what runs an earlier step, the step list,
  how a note is written, and the coverage counts.
- **More invisible characters are caught.** Walkdown already removed zero-width spaces, direction
  controls, soft hyphens, and Unicode tag characters before it read a line. It now also removes and
  reports the Mongolian vowel separator (U+180E, which an outside note named; it was reported as a tag
  character and left in the text), the combining grapheme joiner, the deprecated format controls,
  the interlinear annotation marks, the musical and shorthand format controls, the Arabic letter
  mark, letters and cells that draw as a blank (the Hangul fillers, two Khmer vowels, the blank
  braille cell), and runs of variation selectors. One variation selector after an emoji or a CJK
  character is ordinary and is left alone; two or more in a row are removed and reported, because a
  run of them can hide bytes after one visible character. Zero-width characters between the
  selectors do not break the run, and the text a run spells is read from its selectors alone (a
  Mongolian selector among them is skipped). When the bytes spell readable text, the report shows
  that text on all three pages (`full.md`, `details.html`, and the cards of `review.html`, as it
  does for tag characters) and the phrase check reads it. So a keyword split by one of these now
  matches, and a line hidden by them now shows up as hidden text. The review page shows every one of
  these characters as `U+XXXX` in a card's lines (a variation selector only where two or more stand
  together, so an emoji with its one selector reads as before). The pages call them "blank letters and cells" and "runs of variation selectors", and a
  line with several kinds names them all ("invisible characters and text-direction controls";
  "invisible characters, blank letters and cells, and runs of variation selectors"), where it
  showed the raw kind names. A report line that said "the tag characters spell ..." now says "the
  hidden characters spell ...". The blank braille cell and the fillers can be ordinary in a
  repository with braille-drawn graphs or Korean text, so a finding for them may be harmless.
- **The secret scan no longer skips files without saying so.** On Windows, a file holding a character
  the machine's code page lacks (U+274C, U+1F4DD, a Unicode tag character) got no scan by detect-secrets
  and no error, and the page still said it was checked. On any machine the same happened to a file
  that is not UTF-8. Every file now reaches the scanner as Walkdown reads it, so a run can show more
  lines that look like a saved password, key, or token, and quotes on those lines are now hidden as
  they should be. A file the scanner still does not scan, such as an `.svg` or `.css` file it leaves
  out by name, is named under "Passwords and keys" and in `full.md`: "The secret scan could not scan
  1 file, so it may hold one". One such file no longer makes the page say that no scanner was
  available, and it is no longer listed as a committed secret.
- **A comment in the repository no longer silences the secret scan.** A line with `# pragma: allowlist
  secret` was left out with no record. Those comments now change
  nothing, so a run can show more lines. A comment after a value also no longer gets the line marked
  likely not a secret: `api_key = "x"  // note` read as prose and stayed off the summary.
- **The secret scan reads build files and pattern lists.** A key in `package.json`, `.npmrc`, a `Dockerfile`, a compose file, a
  `Makefile`, `pyproject.toml`, `requirements*.txt`, and the like was not looked for, and nothing said so: one in `package.json`'s license
  reached `details.html` and `full.md`. The same went for `.gitignore`, `.gitmodules`, and the other pattern lists. All of them are read
  now, so a run can show more lines. Only lock files are left out, since the hashes in one look like keys, and the pages say which:
  "The secret scan left out 1 lock file, since the hashes in a lock file look like keys, so it may hold one" on `details.html`, and
  "The secret scan left out 1 lock file." in `full.md`.
- **gitleaks is no longer used.** The secret scan ran gitleaks in place of detect-secrets when one was installed. A repository's own
  `.gitleaks.toml` and `.gitleaksignore` steer gitleaks, by its README, so a repository under audit could take its own lines out of the
  scan. A copy on the machine is now ignored, so a run on such a machine can show other lines. The scan is detect-secrets, plus
  Walkdown's own check for Anthropic keys.

### For someone building it

- **The secret scan's scope is its own list.** `secret_scan.LOCK_FILES`, and `secret_left_out` on `02.4-phrases`'s report. `audience` does not
  move. `ToSend.read` no longer asks a name, `readtext.pattern_list` is new, and `terms.code` moves.
- **The mask of a flagged line reaches every step.** `secretmask.mask_reports`, `mask_copies`, and `mask_edges`, `pipeline.mask_saved`,
  `drift._hide`, and `span` and `event_line` on the findings a parser makes (`02.1-inventory`'s `spans.py`; `trig.*` and `fit.unused`).
  `02.6-builder` masks last, after `fit` has read the tools a grant names. `terms.code` moves.
- **The mask of a flagged line reaches `02.2-reader`.** `secretmask.mask_reader`, `pipeline.mask_saved_reader`, and the report
  stage's `run.load`. A divergence that reaches past its first line has `end_line` (`02.2-reader`'s `reach`), an SVG comment's
  `line` is its first line (it named its last). A masked place's mark key comes from its line, since a hash of the words would
  be one of the secret. `terms.code` moves.
- **What hidden characters spell reaches the pages with no phrase hit.** A line of a file the AI reads whose tag
  characters or variation selectors spell text no pattern matched is a place of its own: a row on `summary.html`
  ("Hidden characters that spell out text"), a card on `review.html`, and the words themselves in `details.html`'s
  list of hidden places, which says it for every hidden place. `full.md` already said it. A tag character between
  variation selectors now reads as one word there ("open"; it read "o p e n").
- **Stop and continue.** `options.add_until_option` and `until_names` (the names come from
  `stages/stages.json`), `pipeline.cut_at` and `run_input_only`, `runner.resume`, and `--input-only` on
  `03-sweep` and `04-pinpoint`. The run's record (`data/run.json`) gains `version`, `until`, `prepared`,
  `code` (a hash of the code a run used, checked by `continue`), and `continued`. Its format is 3 since the check of
  the run (below); a record of format 2 is the record of an earlier version.
  `tool_version` and `code_hash` are `stages/_shared/toolversion.py`. The test run has one wall
  for the whole session, in the test process and in the Python processes a test starts with the environment it inherits (the root
  `conftest.py` and `tests/offline`: no model key, no CLI on the PATH, an SDK stub that ends in a failure, no read of a key from the
  registry); a test that wants a fake brings its own. It is not up in a session started with `--noconftest`, `--confcutdir` or `-c`
  below the root.
- **`--reads`.** `options.ReadsAction`, `reads_plan` (the table as a function of what the machine has), `resolve_reads`, `steps_done`,
  and `Parser` (the one parse error `--reads` can cause, in one sentence). `read_key` moved from `03-sweep/back_jev.py` to
  `stages/_shared/jevkey.py`, which also says whether Jev is available (`back_jev.read_key` is the same function).
- **Shared pieces of the check.** `stagenote.py` (a step's note or warning on one line), `packages.py` (the one list
  of the Python packages Walkdown imports, read by the front door and by the account of a crashed step),
  `common_lines.py` (the phrases the hold and the pages say alike), and `pipeline.read_report`, `own_notes`, and
  `first_finding`. The run's record is format 3 and gains `chosen` (the model reads a command chose), `dropped` (the
  reads an earlier command chose and `continue` left out), and `backends`. A test reads every step's source and the shared
  modules they import, and fails on a write to stderr other than through `stagenote` or an `error:` line just before a failing exit.
- **Layout.** `walkdown.py` only routes. Steps live under `stages/` with `stages/stages.json` as
  the one list of them (name, folder, plain name, heading, option). Code several steps use is in
  `stages/_shared/`, and no step imports another step's module. The report step writes every
  report and reads nothing back out of `LOG.md`.
- **`Library/`.** Tables, lists, and their sources, data only: the patterns (with the plain words
  of each), the word lists, the capability rules, the builder tables, the invisible-character list
  (held by a test to the Unicode default-ignorable property), the base rates, and what the model
  reads show a model. `Library/SOURCES.md` lists each outside
  source once, and the tables cite it by ID. `Library/THREATS.md` and `Library/PHRASES.md` are the
  public reference for the classes and sets the patterns cite. A change to any of it re-measures
  every step's validation stamp.
- **`tools/`.** The grader (`tools/grader/`), `compare_runs.py` (compares two runs, used to check
  that the restructure kept the reports), `baserates.py`, `fixture-generators/`, and
  `model-eval/` (the measured labeling sets, parked for the model work). The grader stops with a
  setup error when an answer sheet's `"stage"` is not the stage its file name says.
- **One spec per step.** Each step folder holds `CONTEXT.md` (a short contract: inputs, process,
  outputs, the human check), `specs/<step>.SPEC.md`, its scripts, and `tests/`. Build briefs and
  how-tos moved to `pre-planning/history/`.
- **Docs.** `CLAUDE.md` is a short router; the build record moved to
  `pre-planning/history/BUILD-RECORD.md`. `docs/STRUCTURE.md` has a second map, of this version,
  beside the 0.3.1 one.
- **Checked.** 2,387 tests pass (2 skipped), and the grader passes every step that has fixtures.

## 0.3.1 (2026-10-27)

summary.html and details.html are rebuilt to be read at a glance, by someone with no computer
skills. Both pages now ask the same eight questions, each with a short label and a one-line
answer: will its skills switch on, how much of the AI's memory it uses, what comes in the
package, will it work on someone else's computer, will it work with AI tools other than Claude,
does it ask only for the tools it needs, is it finished and up to date, and is there anything to
be careful about. There is still no score and no verdict.

- Tokens appear in one place, the memory question, in one table: "Local AI (32k tokens)" and
  "Claude (200k tokens)" ("Your AI" when you set `--context`).
- Plain words throughout, from fixed templates; file names only in small notes. What comes in the
  package is one bar of how the files are used, with the saving if the unused ones were left out.
- The summary quotes the repository only for hidden text that reads like an instruction, up to 80
  characters. details.html quotes every place.
- details.html lists every place by kind, each linked to its card on review.html, and ends with
  what Walkdown didn't check, naming any check skipped for a missing optional tool.
- Marking is on review.html only: the Not concerned boxes on details.html are gone, and both other
  pages say how many places are marked. A marks file saved from those boxes still loads.
- A place counts once, as review.html counts it, on the pages and in the brief, so the numbers
  agree across them.
- A question an older run did not check says "Not measured" (re-rendering an older run draws it
  in the new design).
- Not carried to the new pages: Recommendations, the trifecta's place lists, and the file stats
  (all still in full.md), and Questions before use.

## 0.3.0 (2026-10-27)

The report is rebuilt for people building skills and agents. summary.html now answers, in order:
will it trigger, what it costs, what you ship, will it run on someone else's machine, is it ready
for any AI, do the tools fit the job, is it current and clean, and is it safe. Every yardstick is
a host's documented behavior, dated published guidance, or the skill's own words, kept in dated
data files with sources; there is still no score and no verdict.

- summary.html gains "Is it current and clean?": TODO and FIXME markers, placeholders, and draft
  notes in what ships; claims tied to a date in text the AI reads (published guidance: such text
  becomes wrong); pinned model IDs, with how many are distinct; and older tool names in text. All
  facts with locations; Walkdown never says a date is past or a model retired. "What it costs"
  adds what changed since the earlier run of the same repository (every session, the largest
  entry, what is not used at run time), and the changes in the brief and details.html carry it.
- summary.html gains "Do the tools fit the job?": each skill's, agent's, and command's own words,
  over the files it reads, against the tools it grants. It lists tools granted that nothing asks
  for (a skill's `allowed-tools` as pre-approved and never used), work the words ask for that no
  tool it may use can do (a subagent's tools list is an allowlist), agents with no tools list,
  read-only claims a tool contradicts, loops with no stated limit, and hooks that run on every
  prompt or tool call, with their output's size when it becomes context. A verb a negation
  governs, a verb used as a noun, or a quoted example never counts as asking. details.html and
  full.md list every one; the brief counts.
- summary.html opens with "Will it trigger?": how each skill, command, and agent triggers (Claude
  chooses it by its description, only on matching files, only when typed, or it never loads), the
  descriptions' size against Claude Code's skill listing (about 1% of the context), and what may
  stop it triggering as written: frontmatter its host does not read, agents Claude Code skips, name
  and description rules from the Agent Skills spec, claude.ai uploads, and Claude Code, keys,
  values, and tool names no host takes (with the nearest known one), descriptions that overlap, and
  descriptions cut in the listing. Published guidance (say when to use it; the third person) is
  shown apart from host rules. The rules are a dated data file with sources. details.html and
  full.md list every place; the brief counts. A frontmatter key no host knows now appears here
  instead of under "Is it ready for any AI?".
- summary.html gains "Is it ready for any AI?": one line per AI host (Claude Code, Codex, Gemini
  CLI, Cursor, GitHub Copilot, Windsurf, and the other tools that read `AGENTS.md`) with the
  instruction files, skills, MCP config, and hooks here that it reads, from a dated list of what
  each host reads, with sources. It names the skills no host reads where they sit, copies kept for
  two hosts that say different things (a `CLAUDE.md` and an `AGENTS.md` in one folder), and what
  in a `SKILL.md` or `AGENTS.md` only one host understands: frontmatter keys outside the Agent
  Skills set, Claude Code's own words and tool names, `@` imports in `AGENTS.md`, and hooks.
  `--hosts claude,codex` puts what each named host is missing first. details.html and full.md
  list every one; the brief counts.
- summary.html gains "Will it run on someone else's machine?": the programs and packages a skill
  uses and which the repository never declares (in a dependency file, a skill's `compatibility`
  field, or an install line), and what ties it to the machine it was built on: personal paths,
  shell scripts committed with Windows line endings, scripts or commands for one system only,
  references written with backslashes, scripts run without the executable bit, `python` where
  many systems have only `python3`, and references whose letter case only matches on Windows and
  macOS. Only programs on a dated list count. Line endings are read as git committed them, so a
  Windows checkout's conversion is never blamed on the repository, and personal paths count only
  where they run or the AI reads them. details.html and full.md list every one; the brief counts.
- summary.html is rebuilt for people building a skill or agent: what it costs in an AI's context,
  what you ship, and whether it is safe. What it costs gives the tokens an AI loads every session
  (descriptions, hook text), every session in the folder (CLAUDE.md and what it imports), and for
  the largest skill when it runs, with everything it names, and with its wildcard loads, against
  the context you expect (`--context`, default 32,000 tokens) and 200,000 beside it. What you ship
  sorts every file into loads into the AI, used another way, or not used at run time, and says
  what leaving out the files nothing points to and the build material would save. Tokens are an
  estimate from size (about 4 bytes per token). A skill counts only its own folder, as only that
  installs; what it names outside is listed. Questions before use moved to details.html, which
  gains every file by group. The brief gives the same counts. Measured on Walkdown itself: the
  skill is 558 tokens, CLAUDE.md 3,392 every session.

## 0.2.1 (2026-10-26)

Fixes from an outside tester's report, and the changes merged on GitHub after release 19,
published in public release 20. Newest first.

- Hidden and disguised text is read before matching (found by an outside tester). A
  sentence written in Unicode tag characters is read as the text it spells, and the report
  says what it spells; it had been deleted. Readable text hidden in base64 is decoded and
  matched, and the hit says so; the line is no longer filed as a committed secret. Accents on
  Latin letters are dropped before matching ("ignóre" reads "ignore"). A frontmatter value
  written over several lines (`description: >-`) is matched as one. A host written with
  look-alike letters is listed as written, marked with the host it imitates and its punycode;
  it had been listed as the real host. A new search term, an image address with a template
  slot (`![](https://x/p.png?q={{conversation}})`), is a place under "Reads secrets, calls out,
  or shares". On nine audited repositories nothing changed but one frontmatter hit.
- Less noise on the summary, more secrets found (found by an outside tester). License and
  notice files by other common names (`THIRD_PARTY_NOTICES`, `COPYING`, `CREDITS`, ...) are
  written for people, like `LICENSE`: on a large public skills repository their license text
  had been the example for two concern kinds. A documentation value such as `"abc123..."`, `<your-key>`, or
  `********` is marked as a placeholder, not a committed secret. An Anthropic API key is found
  by its shape whichever scanner is installed (detect-secrets has no rule for one). A link
  definition (`[r1]: path`) counts under Reaching out only when it points at a web address. A
  link written with `%20` for a space resolves, so its target is no longer a broken reference
  and an orphan. Recounted on nine audited repositories: five unchanged; on the other four,
  fewer link-definition hits, and on one, 103 to 97 places with no license-file places or
  placeholder secrets left on its summary.
- Setup and URLs (found by an outside tester on Windows). Started with a Python that lacks
  Walkdown's packages, `walkdown.py` now runs itself again with the `.venv` one before doing
  anything, so version drift and `walkdown.py diff` work there too (they had failed with "No
  module named 'yaml'"). Git never waits for a login: a repository that is not there, or is
  private, stops at once and says so; clones have long paths on and a 10-minute limit; no git
  is said in plain words. A GitHub folder link (`.../tree/<branch>/<folder>`) clones the
  repository at that branch and audits the folder; a file link, or a file, says to give a
  folder. The README has separate Windows and macOS/Linux commands, all with the `.venv`
  Python, names git and Python 3.12 or 3.13, and notes Windows long paths; the walkdown skill
  asks before installing Walkdown's packages when there is no `.venv`.
- summary.html: a line that sends data out is a place. A skill telling the AI to send the `.env`
  file and `~/.aws/credentials` to a URL read as "found none" while full.md cited both lines: the
  pages listed only stage 4's rarest patterns. Now the sending shape (a private source, a
  sending verb, and a destination in one line) is always a place, and a credential named on a
  line that sends is one unless that line is a sending place already. Measured on eight earlier runs: four
  unchanged, the others 1 to 18 more places, all under "Reads secrets, calls out, or shares".
  Found by an outside tester.
- summary.html and the brief: when Walkdown found none of the security concerns it looks for
  but a step that ran did not pass its fixture check, the headline says "but not every step
  worked, so it may have missed some." A failed check had sat under "found none", named only at
  the bottom of the page (found by an outside tester). A check that did not run because an
  optional tool is not installed (INCOMPLETE) is no longer named on summary.html at all, on any
  stage and whether or not the repository has files that tool reads; Other details on
  details.html and full.md still list what it left unread. The brief follows: its list of every
  stage's stamp is one line, "Fixture checks: no step failed." or "Not every step worked in this
  run:" with each step that did not run or failed its check, and never names a missing tool.
- Stage 2, HTML render: the check for Playwright's browser now asks for the exact build this
  Playwright launches (from its own `browsers.json`), not any Chromium. A Chromium left by
  another Playwright version had passed the check, then every HTML file failed to draw; now
  each gets a skip that names the build wanted and the install line. Since static style resolves
  CSS variables, the page-colored variable line in the render fixture is a static-style finding
  (`rd-static-var`); the drawn reading's variable row is now a color set inside `@media`.
- Stage 3, fewer false broken references. A path written as the end of a real one
  (`rules/carousel-rules.md` for `_shared/rules/carousel-rules.md`) now resolves to it, marked
  partial (and ambiguous when several match). A broken reference into a folder the repository
  does not have at all (often `output/`, made when the workflow runs) is listed on its own.
  Measured on six repositories: 14 to 578 fewer broken references each, no orphan hidden by a
  new link (found by an outside tester).
- Stage 5: hidden text pairs with a phrase hit only when the hit's matched words are in the
  hidden text itself, not merely on the same source line. A visible `<pre>` instruction had
  paired with a button label on that line and counted as "Hidden text that reads like an
  instruction" (found by an outside tester). On one audited repository all 11 such pairs stay; on
  another the one that goes was a link's path paired with a badge's alt text.
- Stage 2, HTML: CSS variables are resolved (`var(--x)` and its fallback, inherited as in CSS)
  in text and background colors, and a color or background that cannot be read (a variable
  nobody defines, a gradient, an image) makes no hiding claim. White button text on a
  `var(--acc)` green had been reported as white-on-white against the page (found by an outside
  tester); text colored like the page through a variable is still reported.
- A run that did not complete never reads as clean. When a step produced no output,
  `summary.html` and the brief say "This run did not complete" and name the step, never "found
  none", and the brief says why it stopped (the error's type, and the module of a missing
  import). `walkdown.py` runs the stages with the Python it was started with when that has
  Walkdown's packages, and only then tries the Walkdown folder's `.venv`: an empty `.venv` there
  had been preferred over a working Python, and every step failed (found by an outside tester).
  It says `Using Python at <path>`, and with no usable Python it runs nothing and names what is
  missing.
- Stage 2, image OCR: a large image is read whole as well as in tiles. Tiles alone cut a word
  in large type that straddles a tile edge: re-auditing one repository, its banner's title
  read cut short where the earlier code read it whole. A line read by
  the whole view and a tile is kept once. Re-audit of the four audited repositories at their
  audited commits, old code against new: no finding count, trifecta leg, or install grant
  changed; the new checks found nothing there (no language passages in 4,860 paragraphs, no
  unlisted components, no PDFs; three images now scanned for phrases, no hits).
- With the Tesseract program installed but not the `pytesseract` package, skipped OCR was not
  reported: it now shows under Other details on `details.html`, and at the bottom of
  `summary.html` when the repository has images or PDFs.
- `summary.html`: the line naming a step that did not work moved to the bottom of the page, and a
  missing optional tool (OCR, Playwright) is named there only when the repository has files that
  tool reads. A fresh install without them no longer opens every summary with a warning.
- README: OCR needs the `pytesseract` package as well as the Tesseract program, and what an
  INCOMPLETE stage 2 stamp means without the optional tools (found in a fresh-install test).
- The brief uses the summary page's terms: its headline, one line per concern kind with a count,
  the wording-only line, what the three boxes mean together, and its footer.
- The trifecta line under the boxes no longer says "It is not an issue on its own", and no page,
  doc, or the walkdown skill compares a repository with other repositories ("three checked boxes
  are common in well-built repositories" is gone, and so are HOW-IT-WORKS's "Usually seen"
  notes on what a typical repository shows).
- Docs: HOW-IT-WORKS names the page each kind of finding appears on (`summary.html`,
  `details.html`, `review.html`, `full.md`), and the README says the brief lists the paths to
  every report.

## 0.2.0 (2026-10-20)

Everything since the first alpha, published in public releases 6 to 16 (2026-10-08 to
2026-10-20). Newest first. Every check the method calls for is now built; two optional tools
change what a run finds: Tesseract (text in images and on PDF pages) and Playwright with its
Chromium (HTML as a browser draws it).

- Two pages for two readers. `summary.html` is now one page for deciding whether to use a
  repository: the security concerns Walkdown found, by kind in a fixed order (hidden text that
  reads like an instruction, runs code, looks like a committed secret, reads secrets or calls out
  or shares, lasting changes or permissions) with one example each linked to its review card;
  what it can do; and Questions before use. A step that did not run or did not pass its fixture
  check is named under the headline. It never says to use the
  repository or not, and gives no score. The long page the entries below call the summary page
  is now `details.html`, where "First pass" became those concern rows. `summary.md` and
  `summary-v1.html` are no longer written; re-rendering an older run removes them.
- `details.html` has a Not concerned box on every row that names a place or an address: trifecta
  places, Worth a look files, outside links, hidden places (the count now opens every one),
  secrets, and the places under each risky-ask headline (each headline now opens to them). Ticked
  rows dim, each section counts them, and "Hide Not concerned" folds them away.
- Marks are one set across the pages and carry over. A place marked on `review.html` or
  `details.html` is the same mark, and either page's download keeps the other's. A new run of the
  same repository starts from the newest earlier run's marks, matched by what was flagged (the
  file and the text of the line, or the address), so a mark follows its line when lines move; each
  carried mark names its run. `marks.json` is now
  `walkdown_marks: 2`; files saved earlier still load.
- The tests and graders also run on macOS 15 and Windows Server 2025 on every push.
- Summary page, Hidden text: the count first; hidden text that reads like an instruction in a
  yellow box whose count opens the places, linked to their review cards; and only the lines that
  hold invisible characters or look-alike letters, counted by kind. Typography (curly quotes,
  dashes, ellipses, special spaces) is no longer shown or counted there; the full report keeps
  every changed line.
- Summary page: each checked box of the lethal trifecta opens to the places behind it, each linked
  to its review card or the file. "How it gets in" is gone: MCP servers sit under "Can take outside
  input", the internet under "Can send data out", and the rest under "General risks".
- Comparing two runs no longer counts a file as changed when only its line endings changed (as
  when a checkout converts them); such files are listed apart. When both runs read the same
  commit but files on disk differ, the brief says so instead of crediting every difference to
  Walkdown.
- Summary page: "First pass" groups the places to check by what they could lead to (runs code;
  reads secrets, calls out, or shares; lasting changes or permissions; wording only), and
  "Questions before use" lists the questions the findings raise: permissions to hold back, what
  to try first, and what to settle before leaving it running unattended. Still no verdict.
- Review page: model reads are a separate, optional pass after the rule findings, and "Not sure,
  again" walks just the places you marked Not sure.
- The capability names now start with "Can": "Can read your data", "Can take outside input",
  "Can send data out". A static read shows what a skill could do; only running it shows what it does.
- Review cards end with one line on what only running the skill can show for that kind of place.
- A model read that calls a flagged line something other than an instruction is now shown with
  the finding, on its card and on the summary page ("A reviewer model's reading questions this").
- A line telling the AI to stay read-only, in a skill whose own tools list can write, is now a
  place to check of its own.
- HTML as a browser draws it (the last check listed as not built). With Playwright and its
  Chromium installed, stage 2 draws each HTML file with the page's own scripts off and nothing
  fetched from the network, and reports text a person would not see that static style misses
  (in a closed `<details>` section, moved off the page, clipped or covered, hidden by an `@media` rule, colored like the page
  through a CSS variable), and text a style sheet adds with `::before` or `::after`, which a
  person sees and the model never receives. Without Playwright, HTML is read from static style
  only and the report says so.
- Instructions wrapped across lines: runs of up to four lines of a Markdown paragraph are now
  read as one, and a pattern's exception works across a line break ("don't ask" at the end of
  a line, "hypothetical questions" on the next, is no longer flagged). Review cards mark the
  matched words on every line of a wrapped hit.
- Comparing two runs now says where each new or gone phrase hit came from: the repository (its file
  was added, removed, or edited), Walkdown's search terms (a term added, changed, or retired, named
  in `changes.md`), or Walkdown's matching code. Every stage 4 report records the version of its
  search terms and code (`terms`). Re-auditing the same version of a repository after Walkdown
  changed now reports the differences instead of "nothing to compare", and says they come from
  Walkdown.
- CI runs on Ubuntu 24.04 and 26.04 by name (GitHub moves `ubuntu-latest` to 26.04 from
  2026-10-19), with `actions/checkout` and `actions/setup-python` at v7 (Node 24).
- Stage 3, manifest versus disk, both halves: a skill, agent, or command on disk that its
  manifest leaves out is listed ("On disk, left out of the manifest"), for the kinds the
  manifest names; one that names none relies on its folders and is not compared. A plugin with
  one manifest per host has each compared. On one repository measured, the marketplace names 19 of 20
  skills (the template). Section 7 no longer says manifest versus disk is half built.
- Stage 3: a manifest's paths are read from its plugin root, the folder above `.claude-plugin/`.
  A nested plugin's `"./skills/"` had pointed at the repository's own `skills/` folder, and a
  path that resolved nowhere was dropped (one large repository: 52 fewer dangling references, 57 more
  loads).
- The risky-ask patterns now read PDF, DOCX, and image files, on the text stage 2 read from them
  (the text layer, text drawn on PDF pages, OCR of images). Hits are cited as "extracted text,
  line N". Hidden text in a PDF or DOCX that also reads like an instruction now gets the
  "Hidden, and it reads like an instruction" card. Section 7 no longer lists phrase patterns
  in those files as skipped; a file stage 2 could not read (an image with no Tesseract) is
  still listed. The hosts, confirmations, conditions, and definitions tables still read text
  files only.
- Stage 2 draws each PDF page and reads it (pypdfium2, now a core dependency, plus Tesseract).
  Lines the page shows that its text layer lacks (a picture of an instruction, text drawn as
  shapes, a scanned page) are listed as hidden text, with the page; the language and script
  checks read them. A scanned PDF is read instead of listed as unread. Without Tesseract each PDF is a skip and
  section 7 says so; "PDF render" is no longer "not built". The first 50 pages of each PDF.
- Stage 2, image OCR reads small and faint text better: the image is cropped to its ink, its
  contrast stretched, a dark background inverted, and the crop enlarged; a large image is read
  in tiles, blank ones skipped. 9 px text in the corner of a large image went from 64% of its
  words read to 100%, 8 px light-gray text from 23% to 92%; near-invisible text (`#EEE` on
  white) is still read. 19 of 22 cases in the OCR spike against 17 before
  (`stages/02-reader/OCR-SPIKE-2026-10-18.md`). Tesseract is still the one optional OCR tool:
  the pip-only engine tried missed near-invisible text.
- Stage 2: a language check for text in Latin script (`read.language`). A prose passage whose
  common short words are mostly one other language's (Spanish `el` / `del`, German `und` /
  `der`, and ten more lists), or that is heavily accented with no English in it, is listed with
  the words that matched; the language is never named. Nothing to install: it replaces the
  planned lingua, and section 7 no longer lists language detection as not built. It reads
  Markdown outside code fences, plain text, PDF, DOCX, and OCR text, not code comments, config,
  or HTML. Measured on 1,109 English skill files (20,574 paragraphs): no false positives.
  Recall on short one-line instructions: 16 of 24 held out, misses mostly short Polish, Czech,
  and Turkish lines. The summary's Hidden text section and the full report count and list them.
  New fixture `class04-latin-language.md`.

- Stage 4 now catches an instruction hard-wrapped across two lines of one Markdown paragraph
  (a verb at the end of one line, its target at the start of the next). The finding is cited at
  the line where it starts and quotes both lines. Hits on either line alone are not counted twice.
- Review page: model reads, test data the AI is pointed at, and image cards now say what you are
  deciding ("To decide:"). Test-data and image cards show the line that points the AI at the file
  and what is in it (the start of the file, or the text read from the image). A "do" read says who
  read it and the score in a sentence, and says when it could go either way.
- Stated limits: a line that tells the AI to stay read-only now says whether a tool setting backs it
  (a `--tools` list, deny list, read-only sandbox, or plan mode on the line, or the owner's tools
  list), or that it is stated in the text only, and names other routes in the same skill that can
  write. Review cards show it under "Is it enforced?"; the summary counts it; the full report lists
  every such line and every setting that restricts tools (stage 4 `limit.setting`, stage 5
  `cap.limit`).
- Stage 1: commands in `.cursor/environment.json` (Cursor's cloud-agent setup: `install`, `start`,
  `terminals`) are recorded as commands the host runs on its own, with their lines, and the file is
  an entry point. The report says they run on Cursor's cloud machine, not on your computer.
- Wording: a "do" read from a model now says, beside its score, that it means the line tells the AI
  to do the flagged thing and does not say the thing is harmful (review cards, the summary, and
  docs/MODEL-ACCURACY.md). An agent with no tools list is marked "capability only: what it could use,
  with no evidence it does" on the summary and in HOW-IT-WORKS, and "capability only" in the full report
  (sections 1 and 5).
- `stages/04-phrases/ADDING-A-TERM.md`: the routine for adding, changing, or retiring a search term.
- License: stage 1 records every license file and declared license field (frontmatter,
  `package.json`, plugin manifests, `pyproject.toml`, `Cargo.toml`) and the license its wording
  matches. The summary page says it in one line under the title, with any different license found
  elsewhere; `full.md` section 1 lists them all. Suggested at a class demo.
- Summary page: "Stage by stage" is now "Walkdown Results Breakdown". Each row asks its stage's
  question, says what the step does, and shows its numbers in the open (stage 1: every file type and
  script language); only numbers over 500 characters sit behind "Technical detail". The numbers are
  in plain words, with no repeat of the row's sentence and each term explained (a glob, a dangling
  reference, how text was hidden, what each install grant does). Stage 4 counts lines and says who
  reads them; stage 7 splits not built yet, skipped, and not needed. Reports say "folder or use of
  wildcards" instead of "glob".
- Summary page: "Things to check" now follows "Stage by stage"; the page reads capability,
  stage by stage, things to check, recommendations, model reads.
- Summary page, "What it can do": checked legs first, then unchecked; the checked boxes are
  green, yellow, red in that order, so the third check (all three at once) is the red one.
- Summary page: model reads moved to the end, after the recommendations, in a section closed by
  default that shows how many places it holds.
- Model-read accuracy now has a public page, `docs/MODEL-ACCURACY.md`; the summary page and the
  docs point there.
- Stage 6, Claude backend: reads now run with `--safe-mode` and no setting sources. Before, the
  user's own hooks ran during every read with the audited text in the prompt, and a CLAUDE.md could
  reach the model (found by an outside audit; a live probe confirmed both, and confirms the fix).
- Section 7 tells "not built yet" apart from "tool not installed". PDF page rendering, HTML as a
  browser draws it, and language detection within Latin script have no code; they were reported as
  missing tools, so installing the library would have hidden the gap. A PDF with no text layer is
  always listed as unread.
- Review page (`review.html`, next to `summary.html`): walk through every place to check, one at
  a time, with the lines around it, the matched words highlighted, and what was flagged in plain
  words. Mark each Concerned, Not concerned, or Not sure, with an optional note. Walkdown makes
  no call; the marks are yours. They are kept in the browser, and "Download marks.json" saves
  them; put the file in the run folder and a re-render brings them back. Every search pattern now
  has a plain description. The summary and the review page link to each other at the top right.
- A place named by several findings (three pairs on one line) is one place: one card, counted
  once.
- Stage 4: "don't ask hypothetical questions" (also rhetorical or leading questions, and "no need
  to ask ...") is no longer flagged as skipping confirmation; another "don't ask" on the same line still is
  (owner, 2026-10-12). One audited repository loses 4 hits, and with them its three "loaded only by
  a folder or glob" places (the pressure-test prompts), whose only flagged line this was.
- Stage 4: instruction position in long files (flagged lines past the reader window) and
  sentences repeated across files (REPORTING 4.4, 4.5).
- Stage 4: committed-secret scan (gitleaks when installed, detect-secrets otherwise; new
  requirement). Reported by location only: the value never appears, and other findings on
  that line have their quote replaced.
- Stage 5: images the model is pointed at. An image that a file the model reads references
  or loads (not a README's image, not a manifest icon) is listed under "Things to check",
  with whether this run could read its text. A model with vision reads text in images, so
  the reference is the signal; OCR is extra detail.
- Report wording (owner review 2026-10-07): "Look at these first" is now "Things to check",
  and each card names its section in plain words instead of "Stage N". The "not examined"
  count is now the checks this run skipped that apply to the repository (a missing tool for a
  file type the repository does not ship shows as "not needed"); the full list is unchanged.
  The trifecta is described in plain words on the page. The repeated-sentence card no longer
  shows pattern IDs or "repetition adds weight".
- Stage 4: response limits ("report back with only", "under 15 lines", "only the summary") are
  no longer flagged (`H.report-only` retired).
- Fixes from the 2026-10-08 runs (a large repository showed most of them):
  - A line is called "hidden" only when rendering hides it. A phrase that matches only once
    look-alike or invisible characters are folded reads "disguised with look-alike or invisible
    characters"; a phrase that matches the raw line is no longer paired with an ordinary fold
    such as an en dash (52 of 87 hidden pairs across the runs were these).
  - A few NUL bytes in a UTF-8 file no longer make it binary (one NUL used to skip a whole file,
    including an MCP server's source). NUL is folded like other invisible characters and shown
    as hidden text.
  - Secret hits that hold no secret (a hash under a `sha256` or `hash` key, a password in a URL
    for localhost or a reserved test domain, an environment variable's name, a plain word) are
    counted apart and listed with the reason in the full report only. Files named
    `*.fixtures.*` are test data.
  - The summary's "not examined" line groups unscanned files into one item per section
    instead of naming each file.
  - Stage 4 is fast on files with very long lines: two patterns opened with an unanchored
    lookahead, which is quadratic in line length (a repository with 96,000-character JSON lines:
    stage 4 took 27 minutes, now under 2; the whole run 30 minutes, now 5½). A test keeps
    any pattern from opening that way again.
  - Stage 4 again catches "omit what you changed" (hiding the record of changes), lost when
    response length limits stopped being flagged.
- Cached validation stamps now depend on which optional tools are installed (Tesseract,
  gitleaks, pdf2image, Playwright): installing one re-measures the stages instead of reusing
  a stamp taken without it.

## 0.1.0 (2026-10-04), first alpha

The first version shared for feedback. Stages 1 to 5 and the report are deterministic and
validated against fixtures; stage 6 (model reads) is optional and experimental.

**Running it**
- `python walkdown.py <GitHub URL or folder>` runs every stage and prints a short brief. A URL
  is cloned into `ReposToExamine/`; running it again updates that clone (`--keep` audits it as
  it is, `--fresh` clones again).
- A `walkdown` skill runs it from Claude Code; the brief it relays holds no text from the
  audited repository.
- Each run folder has the reports at the top (`summary.html`, `summary.md`, `full.md`, `LOG.md`)
  and everything else under `data/`.

**What it examines**
- Stage 1, what ships: files, entry points, descriptions, agent tool grants, hooks, manifests,
  MCP servers, structural flags; a content hash per file.
- Stage 2, what the model actually reads: raw text against rendered (hidden HTML, comments,
  zero-width and bidirectional characters, white-on-white, metadata, OCR of images, with small
  images enlarged so tiny text is read).
- Stage 3, what loads what: entry points, orphans, files reached only through globs, dangling
  references.
- Stage 4, what the text asks for: about 125 phrase patterns in four groups, plus tables of
  network hosts, guarded actions and their confirmation steps, conditionals, and definitions.
- Stage 5, what installing it grants: the three legs of the lethal trifecta, install grants,
  bytes in context at load, agent posture, and pairs of findings worth more together.
- Test data (`tests/`, `fixtures/`, `test_*.py` and the like) is set aside from the capability
  map and the summary, and counted; test data a model-read file references still counts.
- Stage 6 (optional): model labels of flagged lines (Jev), relational reads (Claude Code CLI),
  and a coverage sweep for instructions no pattern matched; shown in their own experimental
  block, with "near the line" bands where repeat reads drift.
- Version drift: auditing the same repository again compares the two runs (`changes.md`);
  `walkdown.py diff <old run> <new run>` compares any two.

**How it is checked**
- Every script has a spec and pytest tests (550); every stage has fixtures and a grader.
- The tests and graders run on GitHub on every push (Linux, Python 3.12 and 3.13, Tesseract).
- Each audit stamps each stage's validation in LOG.md; stamps are reused while code and
  fixtures are unchanged (`--revalidate` to measure afresh).

**Known limits**
- English only; static only; known phrasings (the sweep narrows this, experimentally).
- Not built yet: instruction position and repetition checks, secret scanning (gitleaks).
- Stage 6 accuracy is measured and modest (`pre-planning/soft/EVAL.md`); a second human
  labeling of the test lines is in progress.

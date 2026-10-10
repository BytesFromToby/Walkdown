# Tooling: buy vs. build for the hard stages

The hard block (conversions, extraction, deterministic checks) is a solved
problem. Wire in existing, well-maintained libraries rather than rebuild them;
spend the effort on the soft block and the method, which is where the project is
actually novel. This answers the build-vs-buy question flagged in CUSTOMERS.md
and HANDOVER (gap #10).

Organized by stage (METHOD.md, restructured 2026-09-25). Tools for a stage sit
under that stage's heading; "What we build" follows the same order.

## Licensing stance (read first)

Walkdown may be published as portfolio. So the **codebase** stays permissive
(MIT / BSD / Apache). Two popular tools are **AGPL-3.0 and are avoided in the
code**:

- **PyMuPDF (fitz)** — AGPL-3.0. Fast, does text + render + OCR in one, but AGPL
  propagates to anything that imports it (including a hosted tool). *Optional
  accelerator only, behind a pluggable interface — never the default import.*
  (The fixture generators use it; they are dev-only, not part of the shipped tool.)
- **TruffleHog** — AGPL-3.0. Use gitleaks instead.

**GPL command-line binaries invoked as separate processes** (poppler's
`pdftotext` / `pdftoppm`, ExifTool, git) are fine: running a program is not
linking, so they do not propagate to our MIT code. Keep them optional and
documented, and confirm every library's exact license at pin time (licenses
drift; verify, don't trust this table — [[flag-stale-assumptions]]).

## Usable by everyone

The tool must install with `pip` alone. Anything that is not a pip package
(Tesseract, gitleaks, poppler, Playwright browsers, ExifTool) is **optional**:
when it is absent the run does not fail and does not pass silently; the checks
it would have run are listed in stage 7 (Not examined).

## Stage 1: Inventory

| Need | Tool | License | Note |
|---|---|---|---|
| What ships (tracked files, not the working tree) | git (`git ls-files`) | GPL binary | subprocess; zip / tarball inputs walk the extracted tree |
| Magic-byte type | python-magic (libmagic) | MIT | **known noise**: misreports markdown opening with a code fence as JS. Ship the false-positive rate beside the count (REVIEW-2026-09-04) |
| Magic-byte type (pure python) | filetype | MIT | lighter, no libmagic dep, smaller signature set |
| Encoding / BOM detect | charset-normalizer | MIT | |
| Frontmatter parse | PyYAML (`safe_load`) | MIT | plus our own first-colon split, to reproduce each loader a repo ships |
| Manifests, hook configs | stdlib `json` / PyYAML | PSF / MIT | |

## Stage 2: Reader

Conversion (reading A and reading B per format):

| Need | Tool | License | Note |
|---|---|---|---|
| PDF text layer | **pdfminer.six** | MIT | the text a model receives; reading A |
| PDF (simple) | pypdf | BSD | pure-python, fine for trivial extraction |
| PDF render → image (for OCR) | pdf2image (+ poppler `pdftoppm`) | MIT wrapper / GPL binary | reading B; binary is a subprocess; optional |
| OCR | **Tesseract** via pytesseract | Apache-2.0 | images, and PDF reading B; optional |
| OCR a whole PDF | ocrmypdf | MPL-2.0 | adds a text layer to scanned PDFs |
| DOCX | **python-docx** | MIT | body + core properties; also read `word/document.xml` raw via stdlib `zipfile`+`lxml` for A/B |
| PPTX | python-pptx | MIT | all shape text |
| XLSX | openpyxl | MIT | all cells |
| HTML DOM text | **BeautifulSoup4** + lxml | MIT / BSD | reading A |
| HTML rendered/painted text | Playwright | Apache-2.0 | reading B (computed style, `display:none`); heavy, optional |
| SVG | stdlib `xml.etree` / lxml | PSF / BSD | it is XML, not an image |

Fast path if AGPL is ever acceptable (not for publish): PyMuPDF replaces
pdfminer.six + pdf2image + Tesseract wiring in one dependency, 8-12x faster.
Keep it behind the reader interface so it is a drop-in, not a dependency.

Metadata:

| Need | Tool | License | Note |
|---|---|---|---|
| PDF info dict / XMP | pikepdf | MPL-2.0 | |
| DOCX/PPTX/XLSX core props | python-docx / -pptx / openpyxl | MIT | already loaded |
| Image EXIF | Pillow or exifread | HPND / BSD | |
| Everything, one tool | ExifTool via pyexiftool | Perl Artistic+GPL binary / wrapper | optional; subprocess, does not propagate |

Unicode (folded copy and hidden-character counts):

| Need | Tool | License | Note |
|---|---|---|---|
| NFKC fold | stdlib `unicodedata` | PSF | free; the cheapest reader win |
| zero-width / bidi detect | stdlib `unicodedata.bidirectional` + explicit codepoint ranges | PSF | Trojan Source is bidi U+202A-202E / U+2066-2069; zero-width U+200B-200F, U+FEFF, U+2060-2064, U+00AD |
| confusables / homoglyphs (UTS #39 skeleton) | confusable_homoglyphs (or PyICU `SpoofChecker`) | MIT (confirm) / MIT | stdlib does NOT implement the skeleton algorithm; needs a library |
| script blocks (Cyrillic/Greek/CJK runs) | `regex` module `\p{Script=...}` | Apache-2.0 | stdlib `re` has no `\p{Script}`; cheap per-run flag |
| language of a passage | lingua-language-detector (or py3langid) | Apache-2.0 / BSD | handles short + mixed text; for the English-only scope this flags non-English runs |

## Stage 3: Graph

| Need | Tool | License | Note |
|---|---|---|---|
| Reference graph | stdlib dict, or networkx | PSF / BSD | networkx only if the graph work grows |

## Stage 4: Phrases (wire in secrets, don't build)

The clearest "buy" call. The credential / secret class (4a, class 2) is exactly
the hard-fact layer an earlier review said likely exists off the shelf.

| Need | Tool | License | Note |
|---|---|---|---|
| Pattern engine | `regex` module | Apache-2.0 | case-insensitive, over the stage 2 folded copy |
| Secret / credential shapes | **gitleaks** | MIT | fast Go binary, tuned ruleset; subprocess; optional. Prefer over TruffleHog (AGPL) |
| Secrets, python-native | detect-secrets | Apache-2.0 | pip-installable, so the fallback when gitleaks is absent; entropy + patterns |

Do not hand-roll credential regexes when a maintained ruleset exists. Record its
hits like any other detector, with the benign share.

## Stage 6: Soft reads

No tool chosen. The model is the user's choice; the recommendation is a local
model; the final recommendation is deferred pending outside advice (METHOD
stage 6). Whatever runs holds no tools and reads only stage outputs. Without a
model the stage still writes the review packet.

## Prior-art scanners (study / possibly run alongside)

Named in HANDOVER: `safedep/vet`, `cisco-ai-defense/skill-scanner`, and (added
2026-09-24) `NVIDIA/SkillSpector` (Apache-2.0, license-compatible). Worth reading
for their rulesets before building overlapping detectors.

*2026-09-24, third option (undecided, HANDOVER gap 10):* run them **alongside**,
not inside. Their output is not treated as a detector result, because it carries
a verdict (SkillSpector: 0-100 score, SAFE / CAUTION / DO NOT INSTALL). Instead
each of their flags becomes an input the builder report explains, per the
REPORTING.md appendix "Other scanners' flags". Their scores never appear in a
Walkdown report. SkillSpector's optional LLM passes read untrusted skill text; if
it is run, run it with `--no-llm` or treat that as a remote model reading
adversarial text (RED-TEAM §8).

## What we build (the parts no library does)

The libraries above turn bytes into text and flag generic shapes (secrets, magic
type, confusables). Everything below is Walkdown's own. Tag: **[wraps]** =
orchestrates a bought tool; **[ours]** = the logic is the product. Every script
gets `specs/<name>.SPEC.md` and pytest tests and lives in its stage folder
(`stages/NN-name/`). The two early scripts (`tools/extract_urls.py`,
`tools/pass1_normalize.py`) are rebuilt, not retrofitted.

### Foundation
- **Run orchestrator** [ours]: creates `RepoResults/<repo>/<date>_<hash7>/`,
  runs the stages in order, writes each output, and writes each stage's LOG row
  when it finishes. A stage that leaves no mark did not complete. Resumes from
  the first unmarked row.
- **LOG writer + validation-stamp gate** [ours]: a zero is rejected unless the
  same run recorded that the stage's detectors matched their `Fixtures/NN-name/`
  positives. This is what makes a zero trustworthy.
- **Reader / detector interface** [ours]: the thin seam that keeps every bought
  tool a drop-in (the AGPL fast path, a better OCR engine, gitleaks), and lets a
  missing optional tool degrade to stage 7 instead of failing.

### Stage 1: inventory
- **Pin + census** [wraps git + python-magic + charset-normalizer]: tracked-file
  walk, type / size / exec / encoding, entry-point flags, format and
  script-language census, hash pin, structural census (symlinks, size outliers,
  ext-vs-magic with its FP rate, archives, reader-window and long-line outliers).
- **Frontmatter double-parse** [ours]: parse with every loader the repo ships
  (YAML vs first-colon split); record descriptions verbatim and any disagreement.
- **Grant and hook census** [ours]: agent / command tool grants beside their
  stated job; hook event, matcher, blocking, what its script reads.
- **Manifest comparer** [ours]: platform manifests side by side.

### Stage 2: reader (highest value; METHOD: reader beats detector)
- **Reader adapters** [wraps pdfminer.six / python-docx / bs4 / Tesseract / lxml]
  behind the interface, one per format, producing `normalized/text/`.
- **A/B divergence differ** [ours]: diff reading A vs reading B per file, record
  divergence as a fact. No library does this; it is the core reader value.
- **Folder** [wraps unicodedata / confusable_homoglyphs]: NFKC, strip
  zero-width / bidi, fold confusables, into `normalized/folded/`, **keeping a
  line-number map back to the original** [ours].
- **Markdown-carrier extractor** [ours]: hidden reference-link defs, alt text,
  `<details>`, `display:none`, footnotes, fence info strings.
- **Metadata reader** [wraps pikepdf / Pillow / docx core props].
- **Language / script pass** [wraps regex `\p{Script}` + lingua]: flag every
  non-English or non-Latin-script run with its location.

### Stage 3: graph
- **Reference-graph builder** [ours]: nodes and edges from stage 1's entry
  points; orphans, dangling references, dynamic loads, depth, manifest vs disk.

### Stage 4: phrases
- **Pattern engine** [ours]: runs the PHRASES sets over the folded copy by
  sub-group (4a to 4d); records every hit with file:line, verbatim quote,
  audience tag, and benign-share context. The patterns and the base-rate
  discipline are the product.
- **Endpoint census** [ours; replaces `extract_urls.py`]: destinations in code
  and instructions against destinations named in docs.
- **Term-table builder** [ours]: definitions across the union; conflicts,
  safety-vocabulary definitions, displaced-default count. Novel; no prior art.
- **Conditional table, harness rubric, position / repetition** [ours].
- **Secrets adapter** [wraps gitleaks, falls back to detect-secrets].

### Stage 5: capability
- **Capability mapper** [ours]: trifecta on the union, install grants, trust
  elevation paths, cross-stage pairs. Renders least-privilege as a positive
  (Case 002 lesson), not a hit count.

### Stage 6: soft reads
- **Review-packet builder** [ours]: extracts, term rows, the questions.
- **Model runner** [ours, wraps the user's chosen model]: optional; holds no
  tools; records model, prompt, and verbatim output.

### Stages 7 and 8
- **Limits compiler** [ours]: reads the run LOG, the dependency check, and the
  standing-limits list; writes `07-limits.md`.
- **Report assembler** [ours]: `summary.md` + `full.md` in stage order, with the
  standing disclaimers and no verdict.

### Fixtures + grading
- **Grader** [ours]: the **only** component that reads the answer sheet
  (`Fixtures/ANSWERS/`). Built 2026-09-25 at `grader/`. Runs one stage (or all) against its fixtures
  (positives and clean negatives), scores recall and false-positive rate, reports
  pass / fail. This is where "publish the detector's own noise" gets measured.
  Stages are built blind to it (`Fixtures/CONTEXT.md`, independence discipline).
- **Run-time validation gate**: the same fixtures, used inside a real audit (see
  Foundation). Needs only the positives, not the full answer sheet.
- **Fixture manifest / coverage checker** [ours]: every fixture has an ANSWERS
  row, and every detector has at least one positive and one negative fixture.

Build order is owned by HANDOVER "Next actions": fixtures moved into stage
folders and the grader first, then stages 1 to 5 in order, then 7 and 8 with a
thin orchestrator, then 6 once its model is decided.

## The interface principle

Every reader and every hard detector sits behind a thin interface so a tool is a
**drop-in, not a hard dependency**: the AGPL fast path stays swappable, a better
OCR engine slots in, and a wired-in scanner (gitleaks) is one adapter. The method
depends on *what* each stage produces, never on *which* library produced it.

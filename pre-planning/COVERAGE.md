# Coverage matrix: stage → class → detector → fixture

Ties the 22 THREATS classes to the stage that detects them (METHOD.md), the
detector, and the fixture that proves it. **Scope: English skills this
iteration** (CHARTER): the phrase stage goes blind on non-English text, so a
language / script shift is flagged by stage 2 and read by stage 6.

Restructured 2026-09-25. The 2026-09-14 version grouped classes by detection
surface (P / R / S / G / T) and concluded that surface, not the flat 1 to 22, was
the right organizing axis. The seven stages are that conclusion carried through:
surface S became stage 1, R stage 2, G stage 3, P stage 4, and T is a standing
limit in stage 7. Living doc: update the Fixture column as fixtures move and grow.

## How to read it

- **Class numbers are stable tags**, not an ordering. A class split across
  stages has one row per stage, marked (structural half), (phrase half), and so on.
- **Fixture kinds follow the stage.** Stage 1: crafted files, manifests, hooks.
  Stage 2: reader fixtures (input plus expected normalized text and
  divergences). Stage 3: a small repo tree. Stage 4: detector lines that must
  fire, plus clean negatives. Stage 5: fixture repos with a known trifecta.
  Stage 6: hand-labeled soft cases a human scores. Every stage needs clean
  negatives.
- **Answers are grader-only.** Expected results live in `Fixtures/ANSWERS/`,
  never read during a blind build.

## Matrix

| Stage | Class | OWASP | Detector | PHRASES set | Fixture (path under `Fixtures/`) |
|---|---|---|---|---|---|
| **1 Inventory** | 6 Description abuse (description field) | AST04 | frontmatter parse | | `01-inventory/class06-description/` |
| | 9 Cross-platform reuse | AST10 | manifest comparison | | `01-inventory/class09-manifests/` |
| | 15 Second-order (structural half: tool grants) | | frontmatter grants | | `01-inventory/class15-agent-grants/` |
| | 16 Trust elevation (structural half: hook census) | | hook config parse | | `01-inventory/class16-hooks/` |
| | 18 Reader-limit evasion | | measurements | F | `01-inventory/class18-reader-limit/` (symlink deferred: Windows privilege) |
| **2 Reader** | 4 Hidden / obfuscated (invisible, bidi, confusables) | AST08 | A/B reading, folding | K (part) | `02-reader/class04-*` |
| | 4 facet: language / script shift (flag) | | script / language pass | | `02-reader/class04-language-shift.md` |
| | 6 Metadata abuse (metadata fields) | AST04 | metadata read | | `02-reader/class06-metadata.pdf` |
| | 11 Rich formats (human sees vs model reads) | | A/B reading, OCR | | `02-reader/class11-*` (HTML, SVG, PDF, image, DOCX) |
| **3 Graph** | 10 Reference-file indirection | | graph depth | | `03-graph/sample-repo/` |
| | 12 Orphans, dangling refs, dynamic loads | | reachability | | `03-graph/sample-repo/` |
| **4a Reaching out** | 1 Exfiltration channels | AST01 | patterns + endpoint census | K | `04-phrases/class01-exfiltration.md` |
| | 2 Credential / secret access | AST01,03 | patterns + gitleaks | E rollup | `04-phrases/class02-credentials.md` |
| | 3 Remote instruction loading | AST05 | patterns | E rollup | `04-phrases/class03-remote-load.md` |
| **4b Taking the wheel** | 5 Instruction override / persistence | AST01 | patterns | L, H, E | `04-phrases/class05-override.md` |
| | 13 Claimed authorization / consent | | patterns | A | `04-phrases/class13-claimed-consent.md` |
| | 14 Definitional hijacking (hard half: term table) | | patterns + term table | B | `04-phrases/class14-definitional-hijacking.md` |
| | 20 Anti-review / audit-trail (hard half) | | patterns | H | `04-phrases/class20-anti-review.md` |
| | 21 Conditional activation | | patterns + conditional table | I | `04-phrases/class21-conditional.md` |
| **4c Changing the environment** | 7 Execution / privilege | AST03,06 | patterns | E rollup | `04-phrases/class07-execution-privilege.md` |
| | 15 Second-order (phrase half) | | patterns | C | `04-phrases/class15-second-order.md` |
| | 16 Trust elevation (phrase half) | | patterns | D | `04-phrases/class16-trust-elevation.md` |
| | 17 Environment mutation | | patterns | E | `04-phrases/class17-env-mutation.md` |
| | 22 Harness-prohibited actions | | harness rubric | J | `04-phrases/class22-harness-prohibited.md` |
| **4d Talking to the human** | 19 Human-audience / inbound | | patterns + audience tag | G | `04-phrases/class19-human-inbound.md` |
| **5 Capability** | (derived: trifecta, install grants, pairs) | | derivation from 1 to 4 | | none yet |
| **6 Soft reads** | 14 Definitional hijacking (soft half: surprise) | | model read | | none yet (soft cases owed) |
| | 20 Anti-review (soft half: the `silently` case) | | model label | | negatives inside `04-phrases/class20-anti-review.md` |
| | 4 facet: what a shifted passage says | | model read | | `02-reader/class04-language-shift.md` (translation in ANSWERS) |
| **7 Not examined** | 8 Supply chain / drift | AST02,07 | none: snapshot-blind | | version pair owed (future across-runs feature) |

## Fixture status (2026-09-25)

Unchanged in content since 2026-09-14; marker renamed LOAD-BEARING to WALKDOWN
on 2026-09-25 (binary fixtures regenerated from their generators).

- **Stage 1: complete.** Classes 6 (description), 9, 15 and 16 structural halves,
  18 (oversized, long line, ext-magic, BOM, archive, code-fence negative).
  Symlink fixture deferred.
- **Stage 2: complete.** Class 4 (zero-width, bidi, language shift), class 11
  (HTML, SVG, PDF, image / OCR, DOCX), class 6 metadata PDF.
- **Stage 3: complete.** One `sample-repo/` tree: reference indirection (10),
  orphan, dangling ref, dynamic-load glob (12).
- **Stage 4: complete.** Classes 1, 2, 3, 5, 7, 13, 14, 17, 19, 20, 21, 22, and
  the phrase halves of 15 and 16: gate, recall, and negative fixtures.
- **Stage 5: none.** Needs small fixture repos with a known trifecta (0, 1, 2,
  3 legs) and a least-privilege positive.
- **Stage 6: none beyond the negatives above.** Hand-labeled soft cases owed;
  waits on the model decision.
- **Stage 7:** nothing to fixture; its fixture is a run log with a failed stamp
  and a missing dependency, owed with the orchestrator.

**Moved 2026-09-25** from `Fixtures/inputs/{structure,reader,graph,phrase}/` to
`Fixtures/{01-inventory,02-reader,03-graph,04-phrases}/`; the class 6 metadata PDF
moved to `02-reader/`; generators to `Fixtures/_generators/`. The prose answer
sheet became `Fixtures/ANSWERS/<stage>.json` (fixture-hashed), graded by
`grader/grader.py`. Fixed in the move: `longline.md`'s payload sat at column 434,
not past 500 as claimed; now column 525.

## What the matrix exposes

1. **Most of classes 1 to 12 have no dedicated phrase set.** They detect through
   stages 1, 2, and 3, or are rolled into set E. Do not author fixtures assuming
   one regex per class.
2. **Class 8 is snapshot-blind by design.** It lives in stage 7 until the
   across-runs feature exists, and every report names it.
3. **Stages 1 to 3 need non-regex fixtures:** crafted files, reader answer
   sheets (input plus expected normalized text), and a repo tree.
4. **Soft halves (14, 20, the language-shift read) cannot be graded by the
   deterministic grader.** They need hand-labeled soft cases a human scores.
5. **Stage 5 has no fixtures at all.** It derives rather than detects, so its
   fixture is a set of small repos with known answers. Owed before stage 5 is
   built.

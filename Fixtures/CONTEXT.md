# Fixtures — known-answer test inputs (ICM Layer 3: the factory)

Controlled inputs whose correct result is known in advance. They make two rules
enforceable: "validate every detector against a known positive before trusting a
zero," and "a reader is only as good as the documents you test it against."

This is factory (Layer 3), stable across runs. Opposite of `ReposToExamine/`:
those are real artifacts whose result is unknown; these are crafted controls
whose result we set.

## Layout (2026-09-25): one folder per stage

Fixtures are grouped by the stage that must catch them (METHOD.md), and the
inputs and the answers live apart so a stage cannot be built to pass them.

```
Fixtures/
  CONTEXT.md
  01-inventory/      stage 1: one mini repo per class folder (class06, 09, 15, 16, 18)
  02-reader/         stage 2: zero-width, bidi, language shift, HTML/SVG/PDF/image/DOCX, metadata PDF
  03-graph/          stage 3: sample-repo/ (entry points, orphans, dangling ref, glob)
  04-phrases/        stage 4: one file per phrase class, gate / recall / negative sections
  _generators/       scripts that rebuild the binary fixtures (dev-only; not stage input)
  ANSWERS/           the answer sheet: one JSON per stage. GRADER-ONLY.
```

- **`NN-name/`**: the inert test files. Fine to look at; they are just documents.
- **`ANSWERS/`**: expected results per fixture: which checks must fire, which must
  **not**, expected counts, and the reasoning. **Only the grader reads it.** The
  person building a stage does not open it. Format: `ANSWERS/README.md`.
- **The grader** (`../grader/grader.py`) runs `stages/NN-name/run.py` on the
  stage's fixtures and scores the output. Stages report in the format fixed by
  `../stages/CONTRACT.md`, which is visible to builders: it names checks and
  fields, never expected values.
- **Fixture hashes.** ANSWERS records a sha256 per fixture file. Editing,
  adding, or removing a fixture makes the grader refuse to grade that stage until
  its expectations are re-verified and `grader.py --rehash <stage>` is run.
  Regenerating a binary fixture changes its hash too (timestamps), so it needs
  the same step.

## Two kinds of input

- **Detector fixtures** — the smallest input that triggers one detector/class
  (a planted traffic-redirect env line, a `fetch and follow` string).
- **Reader test documents** — whole crafted files that exercise the stage 2
  reader, not just a regex (a PDF whose text layer differs from its render, an
  SVG with `<text>`, a BOM-prefixed file). A hand-typed string never exercises a
  real parser; these do.

## Positives AND negatives (both required)

Every class needs **positives** (must fire) and **clean negatives** (benign lines
that look close but must NOT fire). Positives alone measure only recall; the
negatives are what measure false-positive rate, which is the metric this project
says matters. The "clean test docs" are the negative half.

## Independence discipline (why fixtures come before detectors)

- Author fixtures + `ANSWERS/` from the design corpus (THREATS / PHRASES /
  RED-TEAM / INCIDENTS).
- Build detectors in a **separate session, blind to `ANSWERS/`**, from the
  **class spec** (THREATS/PHRASES class definitions — the detector needs those;
  they are the spec, not the answer key). Judge the detector only by the grader's
  pass/fail, never by eyeballing what was planted.
- Fixtures must be **independent instances**, not the exact example strings copied
  out of PHRASES. Copying the doc string into both the fixture and the detector
  proves nothing.

## What a green eval does and does not mean

Passing the answer sheet proves detectors catch the class **as specified** and
measures their noise on clean inputs. It does **not** prove they catch novel
phrasings of an attack — that is the project's stated blind spot. A green eval is
never "safe."

## Safety rules (non-negotiable — RED-TEAM scope note)

- **Inert. No working payloads, no evasion recipes.** `.invalid` domains, a
  marker on every line. These detect; they are not weapons.
- **Clearly marked as fixtures**, never mistakable for a real artifact.
- **Never placed in `ReposToExamine/` or `RepoResults/`.** Separate home.
- The stage folders contain detection-shaped strings, so a self-audit ("run Walkdown
  on Walkdown") lights up here by design. Exclude `Fixtures/` from self-audit,
  or expect-and-annotate the hits.

## Adding a fixture

1. Put the file in the stage folder that must catch it (a new mini repo folder
   for stage 1). Inert and marked, per the safety rules above.
2. Add its expectations to `ANSWERS/<stage>.json` (positives and negatives),
   with the reasoning in `note`.
3. `python grader/grader.py --rehash <stage>`, then `--check-answers`.
4. If a new check ID is needed, add it to `stages/CONTRACT.md` first.

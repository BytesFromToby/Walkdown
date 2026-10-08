# images.py (added 2026-10-07)

Finds images a model is pointed at. A model with vision reads text in an image, instructions
included, while a person skimming the repository sees a picture. An image reaches the model
only when a file the model reads points at it, so the reference is the signal; OCR (stage 2)
and model reads (stage 6) of the pixels are extra detail. This replaces "every image needs OCR"
as the question the report asks.

## Inputs

Stage 1 (`inv.file`: `ext`, `type`), stage 2 (`read.unread`, `read.divergence` with carrier
`image-text`), stage 3 (`graph.json` edges; `graph.depth` when graph.json is absent). Audience
by path from stage 4's `audience.audience`.

## Outputs

`image_pairs(reports, graph)`: one `cap.pair` with `pair: image+loaded` per image file that a
file with audience `model` or `subagent` references with a static reference or a load
(`kind: static`, or `load: true`). Fields:

- `file`: the image; `from`: the first referencing file (sorted); `froms`: every one.
- `read`: what stage 2 got of its text: `svg` (read from the source), `ocr-text` (OCR found
  text), `ocr-empty` (OCR ran, found none), `unread` (with `reason`, e.g. OCR not installed).
- `evidence`: one row per referencing file and line.

An image is `inv.file` with an image extension (`IMAGE_EXTS`, SVG included) or an `image/`
content type. `run.derive` computes the pairs before test data is set aside, so an image under
tests/ that a model-read file points at still counts.

## Must never

- Pair a reference from a human-facing file (README, docs), a script, or test data.
- Pair a reference in a config file (edge `form: config`, or a `.json`, `.yaml`, `.toml`
  source): a manifest's icon is for the host's UI, not the model (found on superpowers and
  caveman-main, 2026-10-07).
- Pair an image that is only mentioned through a folder or glob (`load: false`).
- Read or decode the image itself: what is in it comes from stage 2.

## Done when (each backed by a test in `tests/test_images.py` or the stage 5 fixtures)

1. A skill's static reference to an image gives the pair, with every referencing file.
2. References from a README, from test data, from a config file, and folder mentions give
   no pair.
3. `read` reports `unread` with the reason, `ocr-text`, `ocr-empty`, or `svg`.
4. Without graph.json, `graph.depth` static records give the pair.
5. Fixture `image-loaded`: the skill's image pairs; the README's banner and the unreferenced
   image do not.

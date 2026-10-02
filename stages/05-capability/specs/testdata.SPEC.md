# testdata.py (added 2026-10-02)

Keeps test data out of the capability map. Fixtures and tests are never loaded as
instructions when an artifact is installed, so their hooks, grants, and phrase hits say
nothing about what installing it grants. (Walkdown's self-audit: its own attack samples lit
every leg and grant.)

## Inputs

Stage 1 to 4 reports. Test data is decided by stage 4's `audience.is_test_data` (path rule).

## Outputs

- `loaded_pairs(reports)`: one `cap.pair` with `pair: testdata+loaded` per `graph.depth`
  finding whose file is test data, `via: static`, and whose `from` is not test data and has
  path audience `model` or `subagent`. `from` names the referencing file.
- `set_aside(reports, loaded)`: a copy of the reports without stage 1 findings on a test-data
  path and stage 4 findings with audience `test-data`, except files in `loaded`; and one
  `cap.testdata` finding counting what was removed (none when nothing was).
- `run.derive` computes the pairs first, then sets test data aside, then derives legs,
  grants, injection, posture, and pairs from what remains.

## Must never

- Drop test data silently: the count is a finding, and stage 7 states the rule.
- Set aside a test-data file that a model-read file references directly.
- Change stage 1 to 4 findings: the set-aside is a copy used only for derivation.

## Done when (each backed by a test in `tests/test_testdata.py` or the stage 5 fixtures)

1. Test data is removed from stages 1 and 4 and counted.
2. Loaded test data is kept and paired; references from human-facing or test files are not.
3. Fixture `testdata-only`: no legs or install grants from samples under tests/.
4. Fixture `testdata-loaded`: the pair appears and the loaded file's text counts.

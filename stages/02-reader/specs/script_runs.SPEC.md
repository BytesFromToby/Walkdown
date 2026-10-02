# script_runs.py: spec

Language / script shift. Stage 2, check `read.script`.

## Inputs

One line of decoded text.

## Outputs

`script_of(ch) -> str`: the Unicode Script property value of one character, by
long name (`Latin`, `Cyrillic`, `Greek`, `Han`, `Common`, `Inherited`, ...), via
the `regex` module's `\p{Script=...}`. `Unknown` when none matches.

`runs(line) -> list[dict]` with `script`, `text`, and `col` (0-based start):

- Only letters (general category `L*`) open or extend a run.
- A letter whose script is Latin, Common, Inherited, or Unknown closes any
  open run and opens none.
- A letter of another script extends the open run when the scripts match, and
  otherwise closes it and opens a new run.
- Non-letters (spaces, digits, punctuation, marks) neither open nor close a
  run. A run's `text` spans from its first letter to its last letter, verbatim.

`script_findings(file, line_no, line) -> list[dict]`: one `read.script`
finding per run (`check`, `file`, `line`, `script`, `text`, plus `col`).

Language detection within Latin script (lingua) is optional in v1 and not done
here; run.py notes its absence on stderr.

## Must never

- Flag accented Latin letters (`café`) or plain ASCII.
- Interpret or translate the run.

## Done when (each backed by a test in `tests/test_script_runs.py`)

1. `script_of` gives Latin, Cyrillic, Greek, Han, Common for sample characters.
2. A Cyrillic sentence with spaces is one run; Latin letters in the middle (`.env`) split it into two runs, each trimmed to its letters.
3. Accented Latin and ASCII give no runs.
4. Adjacent Greek and Cyrillic words give two runs with their own scripts.
5. `script_findings` carries `check`, `file`, `line`, `script`, `text`.

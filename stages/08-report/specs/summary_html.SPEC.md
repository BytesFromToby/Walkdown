# summary_html.py: spec (report v2)

The summary page, rebuilt around a reader's questions (owner redesign, 2026-10-16). Report v1
(the page in stage order) is kept frozen as `summary_v1_html.py` at git tag `report-v1` and
written beside this one as `summary-v1.html` until v2 settles. Same facts as before, from the
fixed rules in `render.py`; nothing new is detected or judged.

## Output

`render_page(meta, reports, stamps, notes, runs_ok, changes_since=None) -> str`: one
self-contained HTML document (`summary.html`). Sections, in the owner's order:

1. **Header.** "Walkdown report on <name>", big, as one line; then source, pin, retrieval date,
   run, and Walkdown version. A link to `review.html` top right, always. No "Static examination
   only" line (owner); the footer keeps `render.NOT_WHAT`.
   Under it, one plain line on the license (added 2026-10-17, class demo feedback): the
   license of each license file at the top level (or in `.claude-plugin/`) with the file, or
   that the file is not a license Walkdown recognizes and how it begins; with no such file, what
   the top-level license fields say; with neither, "No license found". Then "Also stated:" any
   other license found in another file or field, and how many other license files are not
   recognized. Test data is left out. A run made before stage 1 had the check (no
   `license_checked` on `inv.pin`) shows no line. It names the license text a file matches,
   never what the license allows.
2. **The lethal trifecta** (named for what it is, owner). One line credits Simon Willison and
   says what the three mean together. The three legs as a checklist: checked legs first, colored
   green, yellow, red by position (owner decision, 2026-10-12); each checked leg says how many
   places back it (`evidence_total`); a leg whose every cited line a model read as not an
   instruction keeps its box and says so (soft D5). The qualifier (`TRIFECTA_ALL` /
   `TRIFECTA_SOME`) stays. Then **How it gets in**: runs commands on its own (one line per hook),
   adds text to the AI's context before you type (description and startup-hook bytes), lasting
   changes, network, more permissions, MCP servers by name, agents with their own tools (and how
   many have no tools list). What was not found is one "Not found: ..." line.
3. **Files.** Headline in the open: files, file types, total size. **Worth a look**, in the open
   and only when there is something: unknown file type, contents of a different type than the
   name says, archives, symlinks, files the AI reads that are longer than a reviewer's viewer
   shows. Everything else is collapsed under "Files and map": file types and script languages,
   largest files, files a tool loads first, descriptions, manifests, long lines, and the map
   (starting points, how files are reached, files nothing points to by name, broken file
   references, and that the map can miss links).
4. **Outside links.** "Walkdown gathered these and opened none of them." In the open: how many
   links, how many different domains, how many in text the AI reads, how many domains the docs
   never mention. Collapsed: a table grouped by domain with Link | File, line | Read by. A link
   longer than `LINK_SHOW` characters is shortened with "…"; its full address is in the title and
   in a Copy button (copies the whole address). Who reads the file is `READ_BY` over stage 4's
   audience rule. A run made before 2026-10-16 has no addresses saved; its rows show the domain.
5. **Hidden text** (its own section, owner). Where what the AI reads differs from what a person
   sees, by how it was hidden and how many are in files the AI reads; lines changed by folding;
   non-Latin runs; then cards for hidden text that reads like an instruction.
6. **Committed secrets** (its own section, owner). Count, engine, what was set aside (test data,
   likely not secrets); one card per place, value never shown. Skipped when no scanner ran.
7. **Risky asks and things to check.** Overall numbers: lines matched and who reads them, matches
   by kind, the second opinion's split when labels ran, actions that should ask first. Then the
   things to check as a list of headlines with their place counts (hidden text and secrets are
   left to their sections), the model-read count, and the line linking `review.html` when any
   place is listed.
8. **Changes since run X**, only when an earlier run of the same repository is a different
   version (`run.changes_for`): `drift.summary_lines` and a link to `changes.md`. A re-run of the
   same version shows nothing here.
9. **Recommendations (N)**, unranked.
10. **Other details**, collapsed: what was not checked (not built yet, skipped in this run, not
    needed here, every limit behind its own toggle), fixture results per step that ran (a pill
    "N step(s) not passed" on the heading when any is not PASS), and the pointer to `full.md`.

A stage 4 item whose line forbids the matched action (`negated`, review C25) keeps its card with
", stated as a prohibition" (", ... with an exception" when it has a `carve_out`) on its headline;
a rubric row whose action is forbidden (`negated_action`) is never listed as "an irreversible or
prohibited action with no confirmation step", and the risky-asks numbers count it apart ("N where
the text forbids the action"). Test 14.

Every section has words for when it found nothing ("No outside links", "Nothing hidden", "No
lines look like committed secrets", "Nothing to check", "None: no finding matched a
recommendation"), or says it was not checked when its stage did not run.

Theme tokens for light and dark (`prefers-color-scheme` and `data-theme`), phone width with no
page-wide horizontal scroll, every artifact string HTML-escaped (addresses included).

`first_items`, `unique`, and `grouped` are unchanged from v1: `review.html` and the brief in
`walkdown.py` read them.

## Must never

- Show a score, severity, or verdict; drop the trifecta qualifier.
- Emit unescaped text from the artifact.
- Show a secret's value, or open, fetch, or check a link.

## Done when (each backed by a test in `tests/test_summary_html.py`)

1. The sections come in the order above; the title is "Walkdown report on <name>"; no "Static
   examination only" line; dark-theme tokens; the review link top right.
2. Artifact text, including link addresses, is escaped.
3. The trifecta is named, credits Willison, lists checked legs first colored by position, gives
   each checked leg its place count, and keeps the qualifier; a marked leg keeps its box.
4. How it gets in lists each hook on its own line, MCP servers by name, agents with no tools list,
   grants with their counts, and one "Not found" line that keeps "MCP" in capitals.
5. Files: the headline, the "Files and map" toggle, and Worth a look only for the listed kinds
   (long files only when the AI reads them).
6. Outside links: the counts, the table grouped by domain, the full address in title and Copy
   button, shortened display, who reads each file; an older run falls back to domains; empty state.
7. Hidden text: the counts in plain words, the cards, and the empty state.
8. Secrets: the count with engine and what was set aside, a card that shows no value, the empty
   state, and the skipped state.
9. Risky asks: the plain numbers ("the AI", not "a model"), the headline list with place counts
   without the hidden-text and secret headlines, and the review line only when a place is listed.
10. Changes appear only for a different earlier version, with the summary lines and a link to
    `changes.md`.
11. Recommendations have an empty state.
12. Other details is collapsed and holds what was not checked and the fixture results; a step that
    did not pass puts a pill on its heading; a step the run did not include is not listed.
13. No verdict words.
14. A prohibition keeps its card with the headline saying so; it is never called an action with no
    confirmation step; full.md marks it in section 4 and in the rubric table.
15. The header's license line: a recognized top-level file, an unrecognized one with its first
    line, a field when there is no file, "No license found", "Also stated" for a different
    license elsewhere, no test data, and no line for a run without the check.

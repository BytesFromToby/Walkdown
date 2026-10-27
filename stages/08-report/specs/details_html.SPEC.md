# details_html.py: spec

The long page, for someone improving or investigating a repository: every section in full, every
list expandable, and a Not concerned box on every row so the reader can set aside what is fine.

Status: built, renamed from `summary_html.py` / `summary.html` on 2026-10-20; the Not concerned
boxes and place lists built the same day (owner).

Same facts as the other reports, from the fixed rules in `render.py`; nothing new is detected or
judged.

## Inputs

`render_page(meta, reports, stamps, notes, runs_ok, changes_since=None, cap_full=None,
text_href=None, marks=None) -> str`. `cap_full`: stage 5 with every citation (`capability.json`),
for the places under each box; `text_href`: the run's `data/normalized/text` folder relative to
the page, for file links; `changes_since`: `run.changes_for`; `marks`, `carried`: the run's
marks and, when they came from an earlier run, its name (`marks.for_run`).

## Output: `details.html`

Sections in the owner's order. Every section says so when it found nothing, or that it was not
checked when its stage did not run.

1. **Header.** "Walkdown report on <name>" as one line; source, pin, retrieval date, run, and
   Walkdown version; links at the top right to `summary.html` and `review.html` (`HEADER_LINKS`).
   Under it, the license line: the license of each license file at the top level (or in
   `.claude-plugin/`) with the file, or that the file is not one Walkdown recognizes and how it
   begins; with no such file, what the top-level license fields say; with neither, "No license
   found". Then "Also stated:" any other license in another file or field, and how many other
   license files are not recognized. Test data left out. A run made before the license check
   (no `license_checked` on `inv.pin`) shows no line. It names the license a file matches, never
   what the license allows.
   Under the header, the marks bar (`marks_bar`): how to use the boxes, how many rows are marked,
   Hide Not concerned, Download `marks.json`, Load a marks file, and where to save the file.
2. **The lethal trifecta** (`trifecta`). One line credits Simon Willison and says what the three
   mean together. The three boxes as columns, checked first, colored green, yellow, red by
   position (`render.LEG_NAMES`: "Can read your data", "Can take outside input", "Can send data
   out"; `render.LEG_DEFS` under each). Each checked box's "<N> places in the files" opens a
   list of its places (every citation from `capability.json`, up to `SHOWN_PER_LEG`, then a
   count), each linked to its review card when `review.html` shows that file and line, or else
   to this run's copy of the file, with Walkdown's reason in plain words (`_ev_words`). A box
   whose every cited line a model read as not an instruction stays checked and says so.
   What installing it allows (`_allows`): MCP servers by name in the "Can take outside input"
   column and "Connects to the internet" in the "Can send data out" column (`LEG_ALLOWS`); the
   rest under **General risks** (`GENERAL`): runs commands on its own (one line per hook, with
   Cursor's cloud machine named when that is where it runs), adds text to the AI's context before
   you type (description and startup-hook bytes), lasting changes, more permissions, agents with
   their own tools (and how many have no tools list: "capability only"), and one "Not found"
   line. Then the qualifier (`render.TRIFECTA_ALL` / `TRIFECTA_SOME`).
3. **Files.** Headline in the open: files, file types, total size. **Worth a look**, in the open
   and only when there is something: unknown file type, contents of a different type than the
   name says, archives, symlinks, files the AI reads that are longer than a reviewer's viewer
   shows. Collapsed under "Files and map": file types and script languages, largest files,
   files a tool loads first, descriptions, manifests, long lines, and the map (starting points,
   how files are reached, files nothing points to by name, broken file references, and that the
   map can miss links).
4. **Outside links.** "Walkdown gathered these and opened none of them." In the open: links,
   different domains, how many in text the AI reads, domains the docs never mention. Collapsed:
   a table by domain, Link | File, line | Read by; a link longer than `LINK_SHOW` characters is
   shortened with "…", its full address in the title and a Copy button. Who reads the file is
   `READ_BY` over stage 4's audience rule. A run from before 2026-10-16 shows domains only.
5. **Hidden text** (`hidden`). The count of places and how many are in files the AI reads; a muted
   line of their kinds (`CARRIER_PLAIN`). Hidden text that reads like an instruction in one yellow
   box (`_instruction_callout`): its count opens the places, each with its quote and linked to its
   review card. Then a bulleted list: lines that hold invisible characters or look-alike letters,
   counted by kind (`fold_meaning`, `fold_kinds`; typography such as curly quotes, dashes,
   ellipses, special spaces, and symbols is neither shown nor counted, and stays in `full.md`),
   stretches in a non-Latin script, passages in another language written in Latin script.
   The count of places opens the list of every hidden place (`_hidden_rows`, up to
   `SHOWN_PER_LEG`, then a count): where, linked to this run's copy of the file, and how it hides.
6. **Committed secrets.** Count, engine, what was set aside (test data, likely not secrets); one
   row per place with its note, linked to its review card, the value never shown. Skipped when no
   scanner ran.
7. **Risky asks and things to check.** Lines matched and who reads them, matches by kind, the
   second opinion's split when labels ran, actions that should ask first; then the things to
   check as headlines with their place counts (hidden text and secrets are in their own
   sections), any "A reviewer model's reading questions this" lines under their item (up to
   three, then a count), the model-read count, and the review link when any place is listed.
   A line that forbids the matched action keeps its card with ", stated as a prohibition" (", ...
   with an exception" with a `carve_out`); a forbidden rubric action is never listed as one with
   no confirmation step and is counted apart. Each headline opens its places (`_place_row`): the
   location linked to its review card, the quote, and the questioning line when there is one.
8. **Changes since run X**, only when an earlier run of the same repository is a different
   version, or the same version and something differs (`run.changes_for`, `drift.since`): the
   drift summary lines and a link to `changes.md`. With the same commit, it opens by saying so:
   every difference comes from Walkdown when no file on disk differs, otherwise differences in
   other files do.
9. **Recommendations (N)**, unranked.
10. **Other details**, collapsed: what was not checked (not built, skipped in this run, not needed
    here, each limit behind its own toggle), fixture results per step that ran (a pill "N step(s)
    not passed" on the heading when any is not PASS), and the pointer to `full.md`.

**First pass** became the concern rows of `summary.html`, and **Questions before use** moved
there (2026-10-20); `action_group` and `before_use` stay here for it to call.

## Not concerned on every row

Every row that names a place or an address has a **Not concerned** box (`_nc`): the places under
each box of the trifecta, Worth a look files, each outside link (a column of its own, the words
for screen readers), each hidden place, each secret, and each place under a risky-ask headline.
Ticking it records a Not concerned mark for that row's stable key (`marks.SPEC.md`); unticking
clears it (a note stays). A ticked row is dimmed, its section's heading says how many are marked,
and "Hide Not concerned" folds them away. A place's box stands for its review card, so a place
marked on one page is the same mark on the other once both read the same `marks.json`; a place
marked Concerned or Not sure on `review.html` says so beside its box. Carried marks say which run
they are from. Without the script the boxes and the marks bar are hidden.

`mark_rows(r, cap_full)`: every row a mark can name in this run, as (row id, keys): each review
card, each outside link, each Worth a look file, each place under a trifecta box, each hidden
place. Both pages read marks against these rows, and each page's download holds every mark that
matches one, so saving from either page keeps the other page's marks.

## Helpers other outputs read

`first_items`, `unique`, `grouped`: the places, read by `review.html`, `summary.html`, and the
brief in `walkdown.py`; its stage 4 phrase places are `render.point_hits` (2026-10-25, C39). `mark_rows`: read by `review.html`. `action_group`, `before_use`, `header` (with its links), `_allows`,
`GENERAL`, `_place_ids`, and the page's CSS: read by `summary.html`.

## Must never

- Show a score, severity, rank, or verdict; drop the trifecta qualifier.
- Emit unescaped artifact text (addresses included).
- Show a secret's value, or open, fetch, or check a link.
- Write `marks.json`; only the reader saves it. Build markup in the page script from repository
  text (the embedded marks are JSON with "<" escaped).

## Done when (tests in `tests/test_details_html.py`)

1. Sections in the order above; the title; dark-theme tokens; the links top right.
2. Artifact text, link addresses included, escaped.
3. The trifecta: named and credited, checked boxes first colored by position, each checked box's
   places listed and linked, the qualifier kept, a marked box keeps its check
   (`test_trifecta_named_checked_first_colored_with_place_counts`,
   `test_each_box_opens_to_its_places_linked`).
4. MCP servers in the outside-input column, the internet in the send-out column, General risks
   with each hook, agents with no tools list, grants with counts, one Not found line
   (`test_columns_carry_their_installs_and_the_rest_is_general_risks`).
5. Files: the headline, the toggle, Worth a look only for the listed kinds.
6. Outside links: counts, table by domain, full address in title and Copy, shortened display,
   who reads each file; older runs fall back to domains; empty state.
7. Hidden text: the count line and kinds, the callout with its place count and review links, the
   folded lines counted by kind with typography left out, the empty state
   (`test_hidden_text_counts_cards_and_empty_state`,
   `test_fold_line_counts_only_what_can_change_meaning`).
8. Secrets: count with engine and what was set aside, no value shown, empty and skipped states.
9. Risky asks: the plain numbers, the headline list without the hidden-text and secret headlines,
   the questioning-read lines, the review line only when a place is listed.
10. Changes only when they apply, with the same-commit wording.
11. Recommendations empty state; Other details collapsed with its pill.
12. No verdict words; a prohibition keeps its card and is never called an action with no
    confirmation step.
13. The license line: recognized file, unrecognized with its first line, a field, none, Also
    stated, no test data, no line for an older run.
14. A Not concerned box on every row kind, a place's box standing for its review card, the
    hidden places list, each headline opening its places (`test_not_concerned_box_on_every_row`);
    marks one set across the three pages, a link mark kept by a download from `review.html`, a
    carried mark naming its run (`test_marks_are_one_set_across_the_pages`). The page script,
    driven in a browser (2026-10-20): ticking, unticking with a note, the per-section counts, a
    Concerned mark from the review page named beside its box, the download; no horizontal scroll
    at phone width.


## Added 2026-10-25 (review C42, an outside tester)

- A place whose quote holds tag characters notes what they spell ("The hidden tag characters
  spell: ..."), and a stage 4 place decoded from base64 notes the decoded text ("Decoded from
  base64: ..."), before any other note (`_item`); review cards show the same notes.
- Outside links: a domain written with look-alike letters says so on its row, with its
  punycode and the host it imitates (`render.lookalike_note`).

Done when: `test_items_say_what_hidden_text_spells`.

## Added 2026-10-26 (plan for builders, slice 1)

- After the marks bar, "Will it trigger?" (`trigger`, id `trigger`; slice 4): the entries line, the
  listing, every entry with its kind and mode folded, and every place folded under its kind. Done
  when: `test_trigger_section`.
- After it, "What it costs and what you ship" (`ship_section`, id `ship`): the
  expected-context table (`context_table`, also on `summary.html`) with its notes (`cost_notes`:
  the largest skill, what it names outside its folder, how tokens were counted, what only running
  shows), then each band with its groups, every file folded under its group with size, tokens,
  and the file that reaches it. A run with no file groups says so.
- Questions before use (`before_use`) is here again, after the three boxes (owner, 2026-10-26:
  `summary.html` is the builder's page).

Done when: `test_ship_section_and_questions_before_use`.

- After it, "Will it run on someone else's machine?" (`elsewhere`, id `elsewhere`; slice 2): every
  program with where it is declared and its places folded, every package with its ecosystem and
  files, and every place that ties it to one machine folded under its kind. Done when:
  `test_elsewhere_section`.
- After it, "Is it ready for any AI?" (`ready`, id `ready`; slice 3): with `--hosts`, the to-do
  list; every host with the files here it reads folded (instructions, skills, MCP config, hooks),
  or what it would read; the skills to install; every copy kept for two hosts with its relation and
  line counts; every one-host feature folded under its kind. Done when: `test_ready_section`.
- After it, "Do the tools fit the job?" (`fit`, id `fit`; slice 5): how many entries were checked,
  every place folded under its kind, and every hook with how often it runs. Done when:
  `test_fit_section`.
- After it, "Is it current and clean?" (`clean`, id `clean`; slice 6): every place folded under its
  kind, with its line. Done when: `test_clean_section`.

## History

- 2026-10-07: HTML summary page (report v1, now at tag `report-v1`).
- 2026-10-12: review page link; trifecta legs checked first, colored by position (owner).
- 2026-10-16: report v2 in the owner's order (title, trifecta, files, outside links, hidden text,
  secrets, risky asks, changes, recommendations, other details); prohibitions (C25).
- 2026-10-17: license line (class demo feedback); "capability only" (C27).
- 2026-10-19: same-version changes when Walkdown changed (C22 b).
- 2026-10-20: "Can" names (C31 part B); contradicted read-only places (C32); questioning reads
  (C28); First pass and Questions before use (C29); line endings are not edits (drift).
- 2026-10-20: trifecta columns with linked place lists, General risks replaces "How it gets in";
  hidden text reworked, typography left out (owner). Renamed to `details.html`, Not concerned on
  every row, First pass and Questions before use moved to `summary.html` (owner; built the same
  day).

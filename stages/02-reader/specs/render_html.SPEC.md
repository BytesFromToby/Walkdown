# render_html.py: spec (added 2026-10-20)

HTML as a browser draws it. Stage 2's static reader (`read_html.py`) works out what is painted
from inline style and `<style>` rules; a browser also applies `@media` rules, CSS variables,
selectors the static matcher cannot run, positioning, clipping, and elements drawn over others,
and shows text that a style sheet adds with `::before` and `::after`. This module draws each
HTML file in a headless Chromium and reports what a person would and would not see. It was the
last check listed as "not built".

## Inputs

- The input folder (the run's root) and each HTML file's path in it.
- The file's text and the static reader's divergences (to leave out what it already found).

Optional: Playwright and its Chromium (`pip install playwright`, then
`python -m playwright install chromium-headless-shell`). `available()` checks without starting a
browser: the package is importable and the Chromium build it launches is installed, read from
the package's own `browsers.json` (`chromium_headless_shell-<revision>`; 2026-10-21: any
Chromium was enough before, so a build for another Playwright version passed the check and then
failed on every page). A Chromium for another version gives its own reason. When
`browsers.json` cannot be read, any Chromium counts, as before; `PLAYWRIGHT_BROWSERS_PATH` `0`
means the bundled browsers. Without them every HTML file gets a skip. A browser that does not
start gives a skip whose reason is the error's first line only.

## How a page is drawn

- One browser per stage 2 run (`Session`), started at the first HTML file and closed at the
  end; a fresh browser context per file.
- The page's own JavaScript is off; the context is offline; downloads and service workers are
  off; every request is aborted unless it is a `file:` URL inside the input folder, so a page can
  load its own style sheets and images from the repository and nothing else.
- The page is loaded from its file (a 1280 x 800 window, 10 s limit), then a fixed probe runs in
  it. With the page's scripts off, the functions the probe calls are the browser's own.
- At most `MAX_FILES` (200) files are drawn per run; the rest get a skip saying so.

## Outputs

The probe returns, for each text node under `<body>` that a person would not see, its text and
`how` (checked in this order):

| `how` | Meaning |
|---|---|
| `collapsed` | inside a closed `<details>`, outside its summary: on screen only after the reader opens it (one item per section) |
| `not-rendered` | no box at all (`display:none`, including inside `@media`, and the like) |
| `invisible` | `visibility` is not `visible` |
| `transparent` | the element or an ancestor has opacity 0 |
| `zero-size` | every box is under 1 px wide or high |
| `tiny-text` | font size under 2 px |
| `off-page` | every box lies outside the page (left of 0, above 0, or past its width or height) |
| `clipped-or-covered` | at the middle of each box the browser finds another element: the text is clipped by an ancestor or covered (not tested when the text ignores the pointer) |
| `transparent-text` | the text color has alpha 0 |
| `color-matches-background` | contrast with the nearest background color under 1.15 (not judged over a background image) |

and each plain string a `::before` or `::after` adds (three letters or more; counters, `attr()`
and images are not read) as `how` `css-content`.

Form controls (`select`, `option`, `optgroup`, `datalist`, `textarea`) and everything in
`head`, `script`, `style`, `template`, `noscript`, `title` are left out.

`divergences(probe, source, static_texts)` turns that into `{line, text, how, reading}`: hidden
text is `A-only` (the model reads it, a person does not), consecutive text of one element hidden
the same way is one item, and any text that the static reader already reported (either text
inside the other) is left out; generated text is `B-only` with `pseudo`. `line` is where the text
starts in the source (`line_of`: the whole text, its first 40 characters, or its first words with
tags, entities, or white space between), or null.

Stage 2 (`run.html_drawn`) reports each as `read.divergence` with `carrier` `rendered`,
`method` `render`, and `how`. A file not drawn gets a skip with `carrier` `rendered`
(`html not drawn (<why>)`), so the grader skips only the rows about drawn HTML. Coverage gains
`html: {files, drawn}`; without Playwright, `not_examined` lists "HTML as a browser draws it" and
the notes say so.

## Must never

- Run the page's scripts, fetch anything from the network, or read a file outside the input
  folder.
- Report again what static style found.
- Judge what the hidden text means.

## Done when (tests in `tests/test_render_html.py`)

1. `available` is false without the package or without a Chromium, with the reason; with a Chromium build for another Playwright version it is false and says so, and with the build `browsers.json` names it is true.
2. `line_of` finds the line by the whole text, by its start, and across tags and entities, and
   gives null when the text is not in the source.
3. `divergences` merges one element's text, leaves out what static style found (either way),
   and reports generated text as `B-only`.
4. The request filter lets through only `file:` URLs inside the input folder.
5. With Playwright present: text off the page, clipped, hidden by `@media`, colored like the page
   through a CSS variable, covered, and in a closed `<details>` (its summary visible) is found with
   the right `how`; text a `::after` adds is
   `B-only`; visible text and text far down a long page are not reported; a page script that
   would reveal or add text does not run.
6. Without Playwright, an HTML file gets the `rendered` skip and the run says so (`tests/test_run.py`).

Measured 2026-10-20: Compound Engineering at 7a68002, 10 HTML files, 6 findings, all closed
`<details>` sections in plan pages (before `collapsed` existed, the same text gave 114
`clipped-or-covered` findings, one per text node: Chrome lays a closed section out and paints
nothing there); superpowers at bb92a77, 1 file, none.

Fixture: `Fixtures/02-reader/class11-html-render.html` (grader rows `rd-render-*`; the drawn rows
are skipped without Playwright).

# read_html.py: spec

HTML readings A and B from static style. Stage 2, check `read.divergence` for
HTML. Nothing in the page runs; no URL is fetched.

## Inputs

The decoded text of one HTML file.

## Outputs

`read_html(text) -> {"divergences": [...], "painted": [str]}`.

Reading A is all DOM text plus comments and the attributes `alt`, `title`,
`aria-label`. Reading B is the text a browser would paint, from static style:

- Style sources: `<style>` rules (selectors matched with soupsieve, cascade by
  specificity then source order; at-rules skipped) and inline `style`
  attributes (win over rules). Unmatchable selectors are ignored.
- An element is not painted when it or an ancestor has `display:none`,
  `visibility:hidden` (inherited, a child may set `visible`), the `hidden`
  attribute, `opacity:0`, or `font-size:0`; or its text color (inherited,
  default black) `hides` against its effective background (nearest ancestor
  or self with a background color, default white) per `colors.py`.
- `<head>` content, `<title>`, `<script>`, `<template>`, and `<noscript>` are
  not painted. `<style>` content is CSS, not text, and is in neither reading.

Each divergence is `{line, text, carrier}` (reading `A-only`): `text` is the
hidden text with whitespace runs collapsed to one space; `line` the source line
of the element (or of the comment); carriers `display:none`,
`visibility:hidden`, `hidden`, `opacity:0`, `font-size:0`, `white-on-white` /
`color-matches-background` / `transparent`, `comment`, `alt`, `title`,
`aria-label`, `script`, `document-title`, `head`, `template`, `noscript`.
Consecutive hidden text under the same hiding element is one divergence. A
candidate whose text equals a painted text block is dropped (it is in both
readings).

`painted`: the painted text blocks, whitespace collapsed, in document order.

## Must never

- Run a script, load a stylesheet or image, or fetch a URL.
- Interpret the hidden text.

## Done when (each backed by a test in `tests/test_read_html.py`)

1. A class rule `display:none` and an inline `display:none` hide their text, reported with the element's line.
2. White-on-white via a class rule setting `color` and `background` is reported as `white-on-white`; visible text is not reported.
3. `alt`, `title`, and `aria-label` values and comments are reported with their carriers and lines.
4. `visibility:hidden` on a parent with a `visible` child reports only the parent's own text.
5. A `<title>` equal to a painted heading is not reported; any other `<title>` is reported as `document-title`.
6. The `hidden` attribute is reported; painted text appears in `painted`.

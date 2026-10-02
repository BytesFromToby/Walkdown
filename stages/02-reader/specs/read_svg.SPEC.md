# read_svg.py: spec

SVG readings A and B. Stage 2, check `read.divergence` for SVG. SVG is XML
text, not an unread image.

## Inputs

The bytes of one SVG file.

## Outputs

`read_svg(data) -> {"divergences": [...], "painted": [str]}`, or raises
`SvgError` when the XML is not well-formed.

Parsed with lxml with entity resolution, DTD loading, and network access off.
Reading A: every text node, including `<title>`, `<desc>`, `<metadata>`,
`<script>`, comments (also those before the root element), and every `<text>`.
Reading B: painted `<text>` only.

A `<text>` element (with its `tspan` / `textPath` content) is not painted when:

- it sits inside `defs`, `symbol`, `clipPath`, `mask`, `pattern`, or `marker`
  (carrier `defs`);
- it or an ancestor has `display` `none` or `visibility` `hidden` (attribute
  or inline style; carriers `display:none`, `visibility:hidden`), or `opacity`
  / `fill-opacity` 0 (carrier `opacity:0`);
- its fill (attribute or inline style, inherited, default black) is `none`
  (carrier `fill:none`), transparent (carrier `transparent`), or `hides`
  against the background (carriers from `colors.carrier`).

The background at a `<text>` is the fill of the last `<rect>` earlier in the
document (outside `defs`) that covers the text's `x, y` (percent sizes count as
covering), else white.

Divergences are `{line, text, carrier}`, reading `A-only`, `text` with
whitespace collapsed, carriers also `title`, `desc`, `metadata`, `script`,
`comment`, and `not-rendered` (character data outside any `<text>`, which SVG
does not draw; text in `foreignObject` counts as painted). `<style>` content is
CSS and in neither reading; class-based SVG styling is not resolved in v1. A
candidate whose text equals a painted text is dropped.

## Must never

- Resolve entities, load a DTD, fetch a URL, or run a script.
- Interpret the hidden text.

## Done when (each backed by a test in `tests/test_read_svg.py`)

1. Title, desc, metadata, script, and a comment before the root are reported with carriers and lines.
2. `<text fill="none">`, a transparent fill, and white text on a white page are reported; black text is painted.
3. White text over a covering `#eee` rect is reported; white text over a covering black rect is painted.
4. Text in `defs` and text with `display:none` in style are reported.
5. A title equal to a painted text is dropped; malformed XML raises `SvgError`; an entity declaration is not expanded.

# read_md.py: spec

Markdown reading B: content present in the raw text (reading A) that a
rendered view does not show. Stage 2, check `read.divergence` for markdown.

## Inputs

The decoded text of one markdown file.

## Outputs

`carriers(text) -> list[dict]`, each `{line, text, carrier}` (line 1-based in
the original, where the hidden content starts, or for an HTML element or
attribute the line of its opening tag; `text` the hidden content
verbatim, surrounding whitespace stripped), sorted by position:

| Carrier | What |
|---|---|
| `comment` | HTML comment `<!-- ... -->`; `text` is the inner content. Unterminated: to end of file. Empty comments are skipped |
| `details` | `<details>` body (minus its `<summary>`) when the element has no `open` attribute |
| `hidden` / `display:none` / `visibility:hidden` / `font-size:0` / `opacity:0` | an inline HTML element with the `hidden` attribute or that inline style; `text` is its inner content |
| `alt` | image alt text, markdown `![alt](...)` / `![alt][ref]` or HTML `alt="..."` |
| `link-title` | the title of an inline link or image, `[t](url "title")` |
| `title` | an HTML `title="..."` attribute |
| `reference-definition` | a reference-style link definition line `[label]: url "title"` (footnotes `[^x]:` excluded); `text` the line; extra `used`: whether `[label]` is referenced elsewhere |

Nothing inside a fenced code block, an inline code span, or the YAML
frontmatter at the top of the file is a carrier: a render shows code verbatim.

`comment_count(text) -> int`: the number of `comment` carriers (for the Case
001 comparison).

## Must never

- Report content inside code fences or inline code.
- Interpret the hidden content.

## Done when (each backed by a test in `tests/test_read_md.py`)

1. A one-line and a multi-line comment are reported with their start lines and inner text.
2. A comment inside a fenced code block and inside an inline code span is not reported.
3. A closed `<details>` body is reported without its summary; an `open` one is not.
4. A `<div hidden>` and a `<span style="display:none">` are reported with their carriers.
5. Image alt text, a link title, and an HTML title attribute are reported.
6. A reference definition is reported with `used` true when referenced and false when not; a footnote definition is not reported.
7. Frontmatter is not scanned; `comment_count` counts comments.

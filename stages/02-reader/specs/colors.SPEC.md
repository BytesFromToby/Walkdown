# colors.py: spec

Color parsing and the "text colored as its background" test shared by the HTML,
SVG, PDF, and DOCX readers. No check of its own.

## Inputs

Color strings as they appear in CSS, SVG, or DOCX, or RGB tuples from PDF.

## Outputs

`parse(value) -> (r, g, b, a) | None` with r, g, b in 0-255 and a in 0-1:
`#rgb`, `#rgba`, `#rrggbb`, `#rrggbbaa`, bare 6-digit hex (DOCX `FFFFFF`),
`rgb()` / `rgba()` with numbers or percentages, CSS named colors
(case-insensitive), and `transparent` (alpha 0). `none`, `auto`, `inherit`,
`currentColor`, and anything else unknown give None. `!important` is ignored.

`luminance(rgb) -> float`: WCAG relative luminance.

`contrast(fg, bg) -> float`: WCAG contrast ratio (1 to 21).

`hides(fg, bg) -> bool`: True when `fg` has alpha 0, or when the contrast
ratio of fg against bg is below `MIN_CONTRAST` (1.25: text a reader cannot
tell from its background).

`carrier(fg, bg) -> str`: `transparent` when fg alpha is 0; `white-on-white`
when fg and bg are both light (luminance at least 0.7); otherwise
`color-matches-background`.

`WHITE`: the default background (255, 255, 255, 1).

## Must never

- Raise on an unparseable color; it returns None.

## Done when (each backed by a test in `tests/test_colors.py`)

1. `#fff`, `#ffffff`, `FFFFFF`, `white`, `rgb(255,255,255)`, `rgb(100%,100%,100%)` all parse to white; `transparent` has alpha 0; `none` and `auto` give None.
2. White on white hides with carrier `white-on-white`; white on `#eee` hides; black on white does not.
3. Black on black hides with carrier `color-matches-background`.
4. Contrast of black on white is 21.

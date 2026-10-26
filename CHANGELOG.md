# Changelog

## [0.3.0] - 2026-10-26

The comfortable look becomes the suite's: Folio's and Facet's palette (darker text, firmer borders, nothing pale that
matters), larger caption sizes, a High contrast mode (`theme.manager().set_contrast(True)`), table and header styling,
and Folio's UI scale (automatic is 115%, choices up to 200%). 103 icons (Bivouac's, Folio's and Facet's added; Bivouac's open
book is `book-open`). `theme.current_color`. Apps with their own scaling (Facet draws a 3D view) keep their own `uiscale`.

## [0.2.0] - 2026-10-26

- `theme.set_brand(light, dark, css)`: an app's own colours and extra style rules on top of the suite's theme (Gantry's
  school blue and red), instead of a forked theme. New tokens `warning` and `flag`.
- `widgets.logo_tile` (a logo on a white rounded tile), from Gantry.

## [0.1.0] - 2026-10-26

First extraction, from Quire, Ligature, Gantry and Missive: theme (with Ligature's disabled tint and drawing
styles, Quire's bare text edit and under-the-box drop-down lists), 81 icons (the union of all four apps), translation
core with configurable catalogues, UI scale, dialog fitting, Enter-leaves-the-box, `Page`/`Card`/`Segmented`/buttons/
`scrolling`, and `create_application`.

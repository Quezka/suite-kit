# Changelog

## [0.5.0] - 2026-10-27

Compact by construction, not by zoom: "Automatic" interface size is 100% again (nothing scaled), and the elements are
smaller instead: text is never bigger than 9 pt (the stylesheet's sizes are about 14% smaller), paddings, radii and
icons about 22% smaller, pages and cards use tighter margins. `create_application` no longer takes `min_font_pt`.
80% and 90% stay as choices for anyone who wants it even smaller.

## [0.4.0] - 2026-10-26

- "Automatic" interface size is a compact 85% (the system's size was still too large with the comfortable palette).
  New 80% and 90% choices; 100% and up stay in Settings.

## [0.3.1] - 2026-10-26

- "Automatic" interface size is the system's own size (100%), not 115%: the comfortable look is already larger in its
  palette and captions, and the extra zoom made everything too big. 115% and up stay one choice away in Settings.

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

# Changelog

## [0.13.0] - 2026-11-14

The suite's new look: **Material 3, tonal**, chosen from three concepts. No more liquid glass.

- **Navigation rail** instead of the sidebar: each page an icon with its name under it, the current one a tonal
  pill. The rail is as wide as its longest name needs; in a narrow window (under 600 px) it shows icons only.
- **Tonal colours**: a soft, slightly cool background, white cards with big round corners (28 px) and no borders,
  filled text boxes, rounder buttons with one filled colour for the main action. Text is darker than before.
- **No glass, no see-through windows**: menus, lists and tooltips are solid; the page header gets a solid surface
  once the page scrolls under it. Apps are taken off GNOME Blur my Shell's list (its blur cost every frame).
  The "Glass look" and "See-through windows" settings are gone.
- Calm on purpose (easier to focus): fewer lines and outlines, bigger targets, one filled button per screen.

## [0.12.0] - 2026-11-14

- **Menus open where you click, at any interface size.** On Wayland an app can't know where its window is, so Qt
  pretended it sat in the top-left corner and pushed menus up and left to "keep them on screen", more so the
  bigger the interface size (the screen looks smaller to it). Menus now open at the point asked for
  (`fit.exec_menu`, `fit.popup_menu`; button menus too) and the desktop flips or slides them at the real screen edges.
- **Sidebars fit their text.** `fit.fit_sidebar(frame, base)` measures the title and page names (bigger fonts,
  other languages) and widens the sidebar up to 280 px; under 1000 px of window width it shows icons only.
  The Settings window's list of sections does the same.
- `fit.size_class(width)` and `fit.on_size_class(widget, callback)`: compact / medium / expanded at 600 and
  1000 px, for pages that rearrange themselves as the window is resized.

## [0.11.1] - 2026-11-09

- **Less lag:** an app only sits on Blur my Shell's list while its windows are see-through. The extension's blur
  behind a window is redone by the compositor on every frame, even behind an opaque window, so with see-through
  switched off (as in Quire) scrolling and moving windows lagged for nothing. Turning see-through on or off now
  joins or leaves the list straight away.
- The glass header over a scrolling page draws what's under it at an eighth of the size and keeps it until the
  page moves, instead of grabbing the whole area on every repaint; it also blurs the right part of the page now
  (it was mapped through the wrong widget).

## [0.11.0] - 2026-11-09

The suite's new shared look (one design system for every app, `suite-rs/design/tokens.json`):

- **Neutral greys** instead of blue-tinted backgrounds, sidebars and borders; indigo stays as the one accent colour.
- **Bigger, clearer text** on one type scale shared with the phone apps: body text 16 px, nothing smaller than 13 px;
  titles and buttons follow the same sizes everywhere (the Interface size setting still scales it all).
- The same corner radii and spacing in every app.

## [0.10.0] - 2026-11-09

Real transparency and corners that line up.

- **See-through windows** (Windows Aero / macOS style): where the desktop can blur what's behind a window, main
  windows and dialogs let it show through. Cards stay solid so their words read as well as ever, and the sidebar is the
  most see-through. Windows 11 uses the system's Acrylic, Windows 10 its blur-behind. GNOME has no way for an app to ask
  for this, so it works with the Blur my Shell extension: when it's on, the kit adds the app to its list. Apps get a
  "See-through windows" switch (`ThemeManager.set_see_through`); `QUEZKA_SEE_THROUGH=0/1` forces it off or on. An app
  can opt out with `glass.install(app, see_through=False)`.
- **Nested corners**: one radius for every outer surface (`OUTER_RADIUS` 20: the sidebar, cards, the Settings list and
  its floating header) and one gap (`GAP` 10) between them and from the window's edges. Things inside them get the
  radius minus their padding (`NAV_RADIUS`, `TILE_RADIUS`, menu items), so the curves run side by side. Pages, sidebars
  and rows of cards are lined up automatically as they're polished, in every app.
- The Settings header now floats inset, as wide as the cards, and becomes glass when they scroll under it.

## [0.9.0] - 2026-11-08

Liquid glass done the Apple way (`glass.py`). Backgrounds are plain again: the colour wash is gone, and content cards
are solid. The chrome is glass: menus, the lists that drop down from a box and tooltips blur the real content under
them, a settings section's header floats over its cards and blurs them as they scroll underneath (`GlassHeader`),
and the sidebar floats as an inset panel with a light top edge. On Windows 11 the main window gets the system's own
Mica (a blur of the real desktop) behind its sidebar. Nothing invents a background.

## [0.8.3] - 2026-11-08

`theme.follow(t)`: an app that runs its own theme manager (Facet) tells the kit which theme is showing, so the kit's
widgets (the settings switch, section icons) draw in it and follow its changes.

## [0.8.2] - 2026-11-08

Every app dialog takes the new shape by itself as it first opens (`settings.shape`, called from `fit.install`): its
title shown big on top, roomier margins, at least 440 px wide, and the accept button (Save, OK) filled with the accent.
Dialogs with a title of their own and the Settings window are left alone; `setProperty("shaped", False)` opts out.

## [0.8.1] - 2026-11-08

Settings sections keep their margins (the heading was pushed into the corner).

## [0.8.0] - 2026-11-08

Liquid glass on top of Material 3, on by default: the window shows a soft colour wash (the accent from the top left, a
pink glow at the bottom right) and the sidebar, cards, buttons and boxes are frosted and translucent, with a bright top
edge. `ThemeManager.set_glass(on)` turns it off; High contrast stays solid. Brighter colours: a more vivid indigo, and
tinted backgrounds, with text contrast checked by a test (body text 12:1, hints at least 4.5:1).

New `quezka_ui.settings`: `SettingsWindow` (sections on the left, cards of rows on the right, fits small screens),
`SettingsCard.row/switch/wide`, a Material 3 `Switch` with a checkbox's API, and `dialog_shell` that gives editor dialogs
a title and a primary Save button.

## [0.7.0] - 2026-11-04

The icons are Material Symbols now (`symbols.py`, generated by `tools/make_symbols.py`): outlined, and filled when
selected. Only the diagram notation (entity, relationship, attribute, class, inheritance) stays drawn by hand.

## [0.6.0] - 2026-11-04

A new look for the whole suite. Material 3 is now the kit's own look (it was Quire's add-on): tonal surfaces, a pill for
the current page, borderless cards, round buttons, tabs, sliders and progress bars. High contrast stays as it was. The
typeface is Manrope, shipped with the kit (`fonts.py`). A flick on a trackpad now keeps gliding in every scrolling widget
(`kinetic.py`); a mouse wheel is left alone.

## [0.5.3] - 2026-11-04

Three new icons: `pill`, `wallet`, `dumbbell`.

## [0.5.2] - 2026-11-04

Fixed: changing the interface size and pressing Restart did nothing once a size other than 100% was in use (the new
copy inherited the old `QT_SCALE_FACTOR` and took it for the user's own). A button's menu now opens exactly under the
button, with its left edges lined up, above it when there is no room below, and always on the screen.

## [0.5.1] - 2026-10-27

Fixed: the compact text size only reached some widgets. The desktop's theme (GNOME on Wayland) gives labels, buttons,
menus and lists the system's own 11 pt whatever the application font says, so those stayed "enormous". Every common
widget class now gets the compact font explicitly, after the theme is installed.

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

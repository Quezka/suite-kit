# suite-kit (quezka-ui)

Shared PySide6 toolkit for Quire, Ligature, Gantry, Missive, Bivouac, Natter, Folio, Facet. Started 2026-10-26 from the
copies each app had grown (plan: claude-memory `suite-unification-plan`).

- Run tests: `.venv/bin/python -m pytest -q` (offscreen). Test an app against it with `pip install -e ../suite-kit` in the app's venv.
- Icons: Material Symbols by kit name (`symbols.py`, from `tools/make_symbols.py`), filled when checked. `icons._PATHS` is only the diagram notation, drawn by hand. A name keeps its meaning across apps. "link" is the chain, `arrow-up-right` the arrow.
- Catalogues are the apps': `i18n.configure("<app>.presentation.locales")` before `i18n.install`.
- `i18n.plural` accepts a whole plural or an ending (Ligature and Quire wrote it differently).
- No app code in here: no domain, no file formats, no settings dialogs of one app.
- Releases: bump `__version__`, CHANGELOG, tag `vX.Y.Z`; apps pin the tag.
- Commit as arsdom15@gmail.com.
- The look is Material 3 for everyone (`theme.material`, not applied in high contrast); Facet builds its own sheet at scale and reuses `theme.material`. Font: Manrope, four static weights in `assets/` (OFL), loaded by `fonts.load()` in `create_application`.
- `kinetic.py`: glide after a trackpad flick. Trackpad means a scroll phase (Wayland) or a TouchPad device (X11), never pixel deltas. It feeds the scrollbar's own wheel handling, so per-row lists work.
- Glass (0.9.0, Apple style): plain backgrounds, solid content cards, glass chrome. `theme.glass(t)` styles the floating sidebar and buttons and makes popups' sheet background transparent; `glass.py` paints menus/combo lists/tooltips with a real blur of the window under them (`_Popups`, installed by `create_application`; Facet installs it itself), `GlassHeader` floats over a scroll area and blurs what scrolls under it, and Windows 11 gets Mica. Never add a gradient wash or colour blobs as a background: the user rejected that as "AI slop" (2026-11-08).
- Settings windows: build them from `quezka_ui.settings` (`SettingsWindow.section(title, icon).card().row/switch/wide`); editor dialogs call `dialog_shell(dialog, title)` after their layout is built.
- Shape (0.10): every outer surface uses `theme.OUTER_RADIUS` and sits `theme.GAP` from the window edge and its
  neighbours; inner things use the radius minus their padding. `glass._Edges` lines up pages, sidebars and rows of
  cards when they're polished, so apps don't set their own outer margins or card spacing. See-through windows are
  `glass._SeeThrough` (Acrylic on Windows, Blur my Shell on GNOME, painted fill from `theme.see_through_fill`).

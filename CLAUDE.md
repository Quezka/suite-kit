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
- Glass removed in 0.13.0 (user picked Material 3 tonal, 2026-11-14): `glass.py` only keeps `GlassHeader` (= `Header`, solid on scroll), `_Edges`, and leaving Blur my Shell. Never re-add blur or see-through.
- Settings windows: build them from `quezka_ui.settings` (`SettingsWindow.section(title, icon).card().row/switch/wide`); editor dialogs call `dialog_shell(dialog, title)` after their layout is built.
- Shape: outer surfaces `theme.OUTER_RADIUS` (28 since 0.13), `theme.GAP` apart; inner = radius minus padding. `glass._Edges` lines up pages and rails. Sidebars = M3 navigation rail via `fit.fit_sidebar` (labels under icons; window too low -> labels beside icons, `_SidebarFit.short`; icons only < 720 px since 0.15).
- Split screen (0.15): `fit.clamp_window` caps min size at `SPLIT_WIDTH` 640 x `SPLIT_HEIGHT` 480 -> every app must lay out at 640 wide.
- Kinetic: wheel events reach `QWidgetWindow` first -> filter skips non-`QWidget` (else dedupe ate the widget copy = no glide, bug till 0.15).
- Density (0.14, paddings kept since 0.15): `density.py` scales stylesheet `font-size` pt + height px and the app font by main-window size (`STEPS`: >=1100x760 = 1.0, >=900x640 = 0.92, else 0.85), debounced 250 ms; `ThemeManager.apply` uses it. Borders and radii never scale.
- `pages.PageStack` (0.15): main page stack; each page in a frameless scroll area, min width capped `MAX_MIN_WIDTH` 480; `widget/currentWidget/indexOf/setCurrentWidget` return pages. `flow.Flow`: wrapping row (tiles `fill`, buttons `fill=False`), min = widest item.
- UI scale @ wayland (0.15.1): no `QT_SCALE_FACTOR` (fractional -> combo/menu popups drift, user saw it) -> `density.set_user_scale` scales font, heights + padding; x11/windows still qt factor.

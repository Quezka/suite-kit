# suite-kit (quezka-ui)

Shared PySide6 toolkit for Quire, Ligature, Gantry, Missive, Bivouac, Natter, Folio, Facet. Started 2026-10-26 from the
copies each app had grown (plan: claude-memory `suite-unification-plan`).

- Run tests: `.venv/bin/python -m pytest -q` (offscreen). Test an app against it with `pip install -e ../suite-kit` in the app's venv.
- `icons._PATHS` is the union of every app's icons: no name may change its drawing. Ligature's old "link" arrow is now `arrow-up-right`; "link" is the chain.
- Catalogues are the apps': `i18n.configure("<app>.presentation.locales")` before `i18n.install`.
- `i18n.plural` accepts a whole plural or an ending (Ligature and Quire wrote it differently).
- No app code in here: no domain, no file formats, no settings dialogs of one app.
- Releases: bump `__version__`, CHANGELOG, tag `vX.Y.Z`; apps pin the tag.
- Commit as arsdom15@gmail.com.
- The look is Material 3 for everyone (`theme.material`, not applied in high contrast); Facet builds its own sheet at scale and reuses `theme.material`. Font: Manrope, four static weights in `assets/` (OFL), loaded by `fonts.load()` in `create_application`.
- `kinetic.py`: glide after a trackpad flick. Trackpad means a scroll phase (Wayland) or a TouchPad device (X11), never pixel deltas. It feeds the scrollbar's own wheel handling, so per-row lists work.

# quezka-ui (suite-kit)

The shared interface toolkit of the Quire suite (PySide6): theme and style sheet, line icons, translation
core, UI scale, dialog fitting, "Enter leaves a text box", and the page widgets (`Page`, `Card`, `Segmented`,
buttons, `scrolling`). Quire, Ligature, Gantry and Missive each used to carry their own copy; they drifted.

```python
from quezka_ui.app import create_application

app = create_application(argv, name="Ligature", app_id="io.github.quezka.Ligature",
                         icon=Path("assets/icon.svg"), locale_package="ligature.presentation.locales")
```

Each app keeps its own catalogues (`<locale_package>.ru`, `.it`: `MESSAGES`, `PLURALS`, `NAMES`), icon, domain and
branding; extra icons are added with `icons.register({...})`.

## Using it in an app (while the kit has no remote)

```bash
pip install -e ../suite-kit
```

Once the kit has a Git remote, apps depend on a tag: `quezka-ui @ git+https://github.com/Quezka/suite-kit@v0.1.0`.

## Rules for changing it

- A change here changes every app: run this suite, then each app's suite, before tagging.
- Never rename or redraw an icon that apps use (`icons.register` refuses a different drawing for a name).
- Settings keys (`language`, `ui_scale`, `appearance`) are the same in every app on purpose.
- GPL-3.0-or-later.

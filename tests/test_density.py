from quezka_ui import density


def test_small_windows_get_a_tighter_density():
    assert density.for_size(1366, 768) == 1.0
    assert density.for_size(1366, 700) == 0.92
    assert density.for_size(800, 560) == 0.85


def test_css_scales_text_and_heights_not_padding_borders_or_radii():
    css = "QPushButton { padding: 8px 12px; border: 1px solid red; border-radius: 12px; font-size: 12pt; min-height: 40px; }"
    out = density.scale_css(css, 0.5)
    assert "padding: 8px 12px" in out and "min-height: 20px" in out and "font-size: 6pt" in out
    assert "border: 1px solid red" in out and "border-radius: 12px" in out
    assert density.scale_css(css, 1.0) == css


def test_chosen_scale_on_wayland_goes_through_density_not_qt(monkeypatch):
    from quezka_ui import uiscale
    monkeypatch.setenv("QT_QPA_PLATFORM", "wayland")
    monkeypatch.delenv("QT_SCALE_FACTOR", raising=False)
    monkeypatch.setattr(uiscale, "chosen", lambda: "90")
    uiscale.apply_before_app()
    try:
        assert "QT_SCALE_FACTOR" not in __import__("os").environ and density.factor() == 0.9
        assert "padding: 9px" in density.scale_css("QPushButton { padding: 10px; }")
    finally:
        density.set_user_scale(1.0)

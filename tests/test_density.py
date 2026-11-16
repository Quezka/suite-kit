from quezka_ui import density


def test_small_windows_get_a_tighter_density():
    assert density.for_size(1366, 768) == 1.0
    assert density.for_size(1366, 700) == 0.92
    assert density.for_size(800, 560) == 0.85


def test_css_scales_text_and_spacing_not_borders_or_radii():
    css = "QPushButton { padding: 8px 12px; border: 1px solid red; border-radius: 12px; font-size: 12pt; min-height: 40px; }"
    out = density.scale_css(css, 0.5)
    assert "padding: 4px 6px" in out and "min-height: 20px" in out and "font-size: 6pt" in out
    assert "border: 1px solid red" in out and "border-radius: 12px" in out
    assert density.scale_css(css, 1.0) == css

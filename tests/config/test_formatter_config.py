import pytest

from robocop.config import FormatterConfig


@pytest.mark.parametrize(
    "select",
    [
        ["NormalizeSeparators", "CustomFormatter", "NormalizeNewLines"],
        ["NormalizeSeparators", "NormalizeNewLines", "CustomFormatter"],
        ["NormalizeNewLines", "CustomFormatter", "NormalizeSeparators"],
        ["CustomFormatter", "NormalizeNewLines", "NormalizeSeparators"],
    ],
)
def test_unordered_select(select: list[str]):
    expected_order = ["NormalizeSeparators", "NormalizeNewLines", "CustomFormatter"]
    config = FormatterConfig(select=select)
    assert expected_order == config.selected_formatters()


@pytest.mark.parametrize(
    "select",
    [
        ["NormalizeSeparators", "CustomFormatter", "NormalizeNewLines"],
        ["NormalizeSeparators", "NormalizeNewLines", "CustomFormatter"],
        ["NormalizeNewLines", "CustomFormatter", "NormalizeSeparators"],
        ["CustomFormatter", "NormalizeNewLines", "NormalizeSeparators"],
    ],
)
def test_ordered_select(select: list[str]):
    config = FormatterConfig(select=select, force_order=True)
    assert select == config.selected_formatters()

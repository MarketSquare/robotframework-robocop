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


@pytest.mark.parametrize(
    ("select", "extend_select", "expected", "not_expected"),
    [
        # --select with 2, --extend-select with 1; finally we have all 3
        (
            ["NormalizeSeparators", "CustomFormatter"],
            ["NormalizeNewLines"],
            ["NormalizeSeparators", "CustomFormatter", "NormalizeNewLines"],
            ["AlignVariablesSection"],
        ),
        # --select and --extend-select have the same formatter
        (
            ["NormalizeSeparators", "CustomFormatter"],
            ["NormalizeNewLines", "NormalizeSeparators"],
            ["NormalizeSeparators", "CustomFormatter", "NormalizeNewLines"],
            ["AlignVariablesSection"],
        ),
        # no --select, only --extend-select
        ([], ["CustomFormatter"], ["NormalizeSeparators", "CustomFormatter", "AlignVariablesSection"], []),
    ],
)
def test_extend_select(select: list[str], extend_select: list[str], expected: list[str], not_expected: list[str]):
    config = FormatterConfig(select=select, extend_select=extend_select)
    selected_formatters = config.selected_formatters()
    assert all(item in selected_formatters for item in expected)
    assert all(item not in selected_formatters for item in not_expected)

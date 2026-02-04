import pytest

from robocop.runtime.resolver import FormattersLoader


@pytest.mark.parametrize(
    "select",
    [
        ["NormalizeSeparators", "CustomFormatter", "NormalizeNewLines"],
        ["NormalizeSeparators", "NormalizeNewLines", "CustomFormatter"],
        ["NormalizeNewLines", "CustomFormatter", "NormalizeSeparators"],
        ["CustomFormatter", "NormalizeNewLines", "NormalizeSeparators"],
    ],
)
def test_unordered_select(select: list[str], empty_config):
    expected_order = ["NormalizeSeparators", "NormalizeNewLines", "CustomFormatter"]
    loader = FormattersLoader(
        select=select,
        extend_select=[],
        configure=[],
        force_order=False,
        allow_disabled=False,
        target_version=empty_config.target_version,
        skip_config=empty_config.formatter.skip_config,
        whitespace_config=empty_config.formatter.whitespace_config,
        languages=empty_config.languages,
    )
    assert expected_order == loader.selected_formatters()


@pytest.mark.parametrize(
    "select",
    [
        ["NormalizeSeparators", "CustomFormatter", "NormalizeNewLines"],
        ["NormalizeSeparators", "NormalizeNewLines", "CustomFormatter"],
        ["NormalizeNewLines", "CustomFormatter", "NormalizeSeparators"],
        ["CustomFormatter", "NormalizeNewLines", "NormalizeSeparators"],
    ],
)
def test_ordered_select(select: list[str], empty_config):
    loader = FormattersLoader(
        select=select,
        extend_select=[],
        configure=[],
        force_order=True,
        allow_disabled=False,
        target_version=empty_config.target_version,
        skip_config=empty_config.formatter.skip_config,
        whitespace_config=empty_config.formatter.whitespace_config,
        languages=empty_config.languages,
    )
    assert select == loader.selected_formatters()


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
def test_extend_select(
    select: list[str], extend_select: list[str], expected: list[str], not_expected: list[str], empty_config
):
    loader = FormattersLoader(
        select=select,
        extend_select=extend_select,
        configure=[],
        force_order=True,
        allow_disabled=False,
        target_version=empty_config.target_version,
        skip_config=empty_config.formatter.skip_config,
        whitespace_config=empty_config.formatter.whitespace_config,
        languages=empty_config.languages,
    )
    selected_formatters = loader.selected_formatters()
    assert all(item in selected_formatters for item in expected)
    assert all(item not in selected_formatters for item in not_expected)

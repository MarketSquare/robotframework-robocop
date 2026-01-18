from pathlib import Path
from textwrap import dedent
from unittest.mock import Mock

import pytest

from robocop.linter.diagnostics import Position, Range
from robocop.linter.fix import Fix, FixApplicability, FixApplier, FixStats, TextEdit
from robocop.source_file import SourceFile


@pytest.fixture
def mock_config():
    """Create a mock config for testing."""
    config = Mock()
    config.languages = None
    config.linter.fix = True
    config.linter.unsafe_fixes = False
    return config


@pytest.fixture
def sample_source_file(mock_config, tmp_path):
    """Create a sample source file for testing."""
    source_path = tmp_path / "test.robot"
    source_content = dedent("""
        *** Settings ***
        Library    Collections
        Library    String

        *** Test Cases ***
        Test Example
            Log    Hello World
            Should Be Equal    1    1
            Log    Goodbye

        *** Keywords ***
        My Keyword
            [Arguments]    ${arg}
            Log    ${arg}
        """)
    source_path.write_text(source_content)

    source_file = SourceFile(path=source_path, config=mock_config)
    # preload source lines to avoid model loading
    source_file._source_lines = source_content.splitlines(keepends=True)  # noqa: SLF001
    source_file._model = Mock()  # noqa: SLF001 Mock the model to avoid loading

    return source_file


def test_single_line_edit(sample_source_file):
    """Test applying a single-line edit."""
    applier = FixApplier()

    # Change "Hello World" to "Hello Python" on line 7
    edit = TextEdit(
        rule_id="W001",
        rule_name="test-rule",
        start_line=7,
        start_col=12,  # After "Log    "
        end_line=7,
        end_col=23,  # End of "Hello World"
        replacement="Hello Python",
    )
    fix = Fix(edits=[edit], message="Update greeting", applicability=FixApplicability.SAFE)

    applier.apply_fixes(sample_source_file, [fix])

    assert applier.fix_stats.total_fixes == 0  # managed externally
    assert sample_source_file.modified is True
    assert "Hello Python" in sample_source_file.source_lines[6]
    assert applier.fix_stats.by_file[sample_source_file.path][("W001", "test-rule")] == 1


def test_multi_line_edit(sample_source_file):
    """Test applying a multi-line edit that replaces several lines."""
    applier = FixApplier()

    # Replace lines 7-9 with a single line
    edit = TextEdit(
        rule_id="W002",
        rule_name="simplify-test",
        start_line=7,
        start_col=1,
        end_line=9,
        end_col=999,
        replacement="    Log    Single line replacement\n",
    )
    fix = Fix(edits=[edit], message="Simplify test", applicability=FixApplicability.SAFE)

    applier.apply_fixes(sample_source_file, [fix])

    assert applier.fix_stats.total_fixes == 0
    assert sample_source_file.modified is True
    assert "Single line replacement" in sample_source_file.source_lines[6]
    # Original 3 lines replaced with 1, so total lines should be 2 less
    original_line_count = 14
    assert len(sample_source_file.source_lines) == original_line_count - 2
    assert applier.fix_stats.by_file[sample_source_file.path][("W002", "simplify-test")] == 1


def test_fix_with_multiple_edits(sample_source_file):
    """Test a single Fix containing multiple TextEdit instances."""
    applier = FixApplier()

    # Multiple edits in one fix (non-overlapping)
    edits = [
        TextEdit(
            rule_id="W003",
            rule_name="update-library",
            start_line=2,
            start_col=12,
            end_line=2,
            end_col=23,
            replacement="BuiltIn",
        ),
        TextEdit(
            rule_id="W003",
            rule_name="update-library",
            start_line=3,
            start_col=12,
            end_line=3,
            end_col=18,
            replacement="DateTime",
        ),
    ]
    fix = Fix(edits=edits, message="Update library names", applicability=FixApplicability.SAFE)

    applier.apply_fixes(sample_source_file, [fix])

    assert applier.fix_stats.total_fixes == 0
    assert sample_source_file.modified is True
    assert "BuiltIn" in sample_source_file.source_lines[1]
    assert "DateTime" in sample_source_file.source_lines[2]
    assert applier.fix_stats.by_file[sample_source_file.path][("W003", "update-library")] == 2


def test_overlapping_edits_first_wins(sample_source_file):
    """Test that overlapping edits are handled - first one wins."""
    applier = FixApplier()

    # Two overlapping edits on the same line
    fix1 = Fix(
        edits=[
            TextEdit(
                rule_id="W004",
                rule_name="first-rule",
                start_line=7,
                start_col=12,
                end_line=7,
                end_col=23,
                replacement="First",
            )
        ],
        message="First fix",
        applicability=FixApplicability.SAFE,
    )
    fix2 = Fix(
        edits=[
            TextEdit(
                rule_id="W005",
                rule_name="second-rule",
                start_line=7,
                start_col=12,
                end_line=7,
                end_col=23,
                replacement="Second",
            )
        ],
        message="Second fix",
        applicability=FixApplicability.SAFE,
    )

    applier.apply_fixes(sample_source_file, [fix1, fix2])

    # Only the first edit should be applied
    assert applier.fix_stats.total_fixes == 0
    assert "First" in sample_source_file.source_lines[6]
    assert "Second" not in sample_source_file.source_lines[6]
    assert applier.fix_stats.by_file[sample_source_file.path][("W004", "first-rule")] == 1
    assert ("W005", "second-rule") not in applier.fix_stats.by_file[sample_source_file.path]


def test_overlapping_multiline_edits(sample_source_file):
    """Test overlapping multi-line edits."""
    applier = FixApplier()

    # Two edits with overlapping line ranges
    fix1 = Fix(
        edits=[
            TextEdit(
                rule_id="W006",
                rule_name="first-multiline",
                start_line=7,
                start_col=1,
                end_line=8,
                end_col=999,
                replacement="    First edit\n",
            )
        ],
        message="First fix",
        applicability=FixApplicability.SAFE,
    )
    fix2 = Fix(
        edits=[
            TextEdit(
                rule_id="W007",
                rule_name="second-multiline",
                start_line=8,
                start_col=1,
                end_line=9,
                end_col=999,
                replacement="    Second edit\n",
            )
        ],
        message="Second fix",
        applicability=FixApplicability.SAFE,
    )

    applier.apply_fixes(sample_source_file, [fix1, fix2])

    # Only the first edit should be applied (they overlap on line 8)
    assert applier.fix_stats.total_fixes == 0
    assert "First edit" in sample_source_file.source_lines[6]
    assert applier.fix_stats.by_file[sample_source_file.path][("W006", "first-multiline")] == 1


def test_manual_fix_not_applied(sample_source_file):
    """Test that MANUAL fixes are not applied."""
    applier = FixApplier()

    edit = TextEdit(
        rule_id="W009",
        rule_name="manual-rule",
        start_line=7,
        start_col=12,
        end_line=7,
        end_col=23,
        replacement="Manual change",
    )
    fix = Fix(edits=[edit], message="Manual fix", applicability=FixApplicability.MANUAL)

    applier.apply_fixes(sample_source_file, [fix])

    assert applier.fix_stats.total_fixes == 0
    assert sample_source_file.modified is False


def test_mixed_applicability_only_safe_applied(sample_source_file):
    """Test mix of SAFE, UNSAFE, and MANUAL fixes - only SAFE applied."""
    applier = FixApplier()

    fixes = [
        Fix(
            edits=[
                TextEdit(
                    rule_id="W010",
                    rule_name="safe-rule",
                    start_line=2,
                    start_col=12,
                    end_line=2,
                    end_col=23,
                    replacement="SafeLib",
                )
            ],
            message="Safe fix",
            applicability=FixApplicability.SAFE,
        ),
        Fix(
            edits=[
                TextEdit(
                    rule_id="W011",
                    rule_name="unsafe-rule",
                    start_line=3,
                    start_col=12,
                    end_line=3,
                    end_col=18,
                    replacement="UnsafeLib",
                )
            ],
            message="Unsafe fix",
            applicability=FixApplicability.UNSAFE,
        ),
        Fix(
            edits=[
                TextEdit(
                    rule_id="W012",
                    rule_name="manual-rule",
                    start_line=7,
                    start_col=12,
                    end_line=7,
                    end_col=23,
                    replacement="ManualChange",
                )
            ],
            message="Manual fix",
            applicability=FixApplicability.MANUAL,
        ),
    ]

    applier.apply_fixes(sample_source_file, fixes)

    assert applier.fix_stats.total_fixes == 0
    assert "SafeLib" in sample_source_file.source_lines[1]
    assert "UnsafeLib" not in sample_source_file.source_lines[2]
    assert "ManualChange" not in sample_source_file.source_lines[6]
    assert applier.fix_stats.by_file[sample_source_file.path][("W010", "safe-rule")] == 1


def test_non_overlapping_edits_all_applied(sample_source_file):
    """Test that non-overlapping edits are all applied."""
    applier = FixApplier()

    fixes = [
        Fix(
            edits=[
                TextEdit(
                    rule_id="W013",
                    rule_name="fix-lib",
                    start_line=2,
                    start_col=12,
                    end_line=2,
                    end_col=23,
                    replacement="Lib1",
                )
            ],
            message="Fix 1",
            applicability=FixApplicability.SAFE,
        ),
        Fix(
            edits=[
                TextEdit(
                    rule_id="W014",
                    rule_name="fix-test",
                    start_line=7,
                    start_col=12,
                    end_line=7,
                    end_col=23,
                    replacement="Test1",
                )
            ],
            message="Fix 2",
            applicability=FixApplicability.SAFE,
        ),
        Fix(
            edits=[
                TextEdit(
                    rule_id="W015",
                    rule_name="fix-keyword",
                    start_line=12,
                    start_col=12,
                    end_line=12,
                    end_col=18,
                    replacement="Keyword1",
                )
            ],
            message="Fix 3",
            applicability=FixApplicability.SAFE,
        ),
    ]

    applier.apply_fixes(sample_source_file, fixes)

    assert applier.fix_stats.total_fixes == 0
    assert "Lib1" in sample_source_file.source_lines[1]
    assert "Test1" in sample_source_file.source_lines[6]
    assert "Keyword1" in sample_source_file.source_lines[11]
    assert applier.fix_stats.by_file[sample_source_file.path][("W013", "fix-lib")] == 1
    assert applier.fix_stats.by_file[sample_source_file.path][("W014", "fix-test")] == 1
    assert applier.fix_stats.by_file[sample_source_file.path][("W015", "fix-keyword")] == 1


def test_empty_fixes_list(sample_source_file):
    """Test applying an empty list of fixes."""
    applier = FixApplier()

    applier.apply_fixes(sample_source_file, [])

    assert applier.fix_stats.total_fixes == 0
    assert sample_source_file.modified is False
    assert applier.fix_stats.by_file == {}


def test_edits_sorted_correctly(sample_source_file):
    """Test that edits are sorted and applied in the correct order."""
    applier = FixApplier()

    # Provide fixes in reverse order - they should be sorted
    fixes = [
        Fix(
            edits=[
                TextEdit(
                    rule_id="W016",
                    rule_name="last-fix",
                    start_line=12,
                    start_col=1,
                    end_line=12,
                    end_col=5,
                    replacement="Last",
                )
            ],
            message="Last",
            applicability=FixApplicability.SAFE,
        ),
        Fix(
            edits=[
                TextEdit(
                    rule_id="W017",
                    rule_name="first-fix",
                    start_line=2,
                    start_col=1,
                    end_line=2,
                    end_col=5,
                    replacement="First",
                )
            ],
            message="First",
            applicability=FixApplicability.SAFE,
        ),
        Fix(
            edits=[
                TextEdit(
                    rule_id="W018",
                    rule_name="middle-fix",
                    start_line=7,
                    start_col=1,
                    end_line=7,
                    end_col=5,
                    replacement="Middle",
                )
            ],
            message="Middle",
            applicability=FixApplicability.SAFE,
        ),
    ]

    applier.apply_fixes(sample_source_file, fixes)

    assert applier.fix_stats.total_fixes == 0
    # All should be applied despite being provided out of order
    assert sample_source_file.source_lines[1].startswith("First")
    assert sample_source_file.source_lines[6].startswith("Middle")
    assert sample_source_file.source_lines[11].startswith("Last")


def test_fix_stats_multiple_same_rule(sample_source_file):
    """Test that statistics correctly count multiple fixes from the same rule."""
    applier = FixApplier()

    # Multiple edits from the same rule
    edits = [
        TextEdit(
            rule_id="I001",
            rule_name="unsorted-imports",
            start_line=2,
            start_col=12,
            end_line=2,
            end_col=23,
            replacement="Lib1",
        ),
        TextEdit(
            rule_id="I001",
            rule_name="unsorted-imports",
            start_line=3,
            start_col=12,
            end_line=3,
            end_col=18,
            replacement="Lib2",
        ),
    ]
    fix = Fix(edits=edits, message="Sort imports", applicability=FixApplicability.SAFE)

    applier.apply_fixes(sample_source_file, [fix])

    assert applier.fix_stats.total_fixes == 0
    assert applier.fix_stats.by_file[sample_source_file.path][("I001", "unsorted-imports")] == 2


def test_fix_stats_merge(tmp_path, mock_config):
    """Test merging multiple FixStats together."""
    # Create two different source files
    file1 = tmp_path / "file1.robot"
    file1.write_text("*** Test Cases ***\nTest 1\n    Log    1\n")
    source1 = SourceFile(path=file1, config=mock_config)
    source1._model = Mock()  # noqa: SLF001

    file2 = tmp_path / "file2.robot"
    file2.write_text("*** Test Cases ***\nTest 2\n    Log    2\n")
    source2 = SourceFile(path=file2, config=mock_config)
    source2._model = Mock()  # noqa: SLF001

    applier = FixApplier()

    # Apply fixes to both files
    fix1 = Fix(
        edits=[
            TextEdit(
                rule_id="I001",
                rule_name="unsorted-imports",
                start_line=3,
                start_col=5,
                end_line=3,
                end_col=8,
                replacement="Log1",
            )
        ],
        message="Fix 1",
        applicability=FixApplicability.SAFE,
    )
    applier.apply_fixes(source1, [fix1])

    fix2 = Fix(
        edits=[
            TextEdit(
                rule_id="I001",
                rule_name="unsorted-imports",
                start_line=3,
                start_col=5,
                end_line=3,
                end_col=8,
                replacement="Log2",
            ),
            TextEdit(
                rule_id="D413",
                rule_name="missing-blank-line",
                start_line=2,
                start_col=1,
                end_line=2,
                end_col=6,
                replacement="Test2Fixed",
            ),
        ],
        message="Fix 2",
        applicability=FixApplicability.SAFE,
    )
    applier.apply_fixes(source2, [fix2])

    assert applier.fix_stats.total_fixes == 0
    assert applier.fix_stats.by_file[file1][("I001", "unsorted-imports")] == 1
    assert applier.fix_stats.by_file[file2][("I001", "unsorted-imports")] == 1
    assert applier.fix_stats.by_file[file2][("D413", "missing-blank-line")] == 1


def test_fix_stats_format_summary_single_file(tmp_path):
    """Test formatting summary for a single file."""
    file1 = tmp_path / "test.robot"

    stats = FixStats(
        total_fixes=3,
        by_file={
            file1: {
                ("I001", "unsorted-imports"): 1,
                ("D413", "missing-blank-line"): 2,
            }
        },
    )

    summary = stats.format_summary()

    assert "[green]Fixed 3 issues:[/green]" in summary
    assert str(file1) in summary
    assert "1 x [red]I001[/red] (unsorted-imports)" in summary
    assert "2 x [red]D413[/red] (missing-blank-line)" in summary


def test_fix_stats_format_summary_multiple_files(tmp_path):
    """Test formatting summary for multiple files."""
    file1 = tmp_path / "file1.robot"
    file2 = tmp_path / "file2.robot"

    stats = FixStats(
        total_fixes=6,
        by_file={
            file1: {
                ("I001", "unsorted-imports"): 1,
                ("D413", "missing-blank-line"): 4,
            },
            file2: {("I001", "unsorted-imports"): 1},
        },
    )

    summary = stats.format_summary()

    assert "[green]Fixed 6 issues:[/green]" in summary
    assert str(file1) in summary
    assert str(file2) in summary
    assert "1 x [red]I001[/red] (unsorted-imports)" in summary
    assert "4 x [red]D413[/red] (missing-blank-line)" in summary


def test_fix_stats_format_summary_no_fixes():
    """Test formatting summary when no fixes were applied."""
    stats = FixStats()

    summary = stats.format_summary()

    assert summary == "No fixes applied."


def test_fix_stats_format_summary_singular():
    """Test formatting summary with exactly 1 issue (singular form)."""
    file1 = Path("test.robot")

    stats = FixStats(total_fixes=1, by_file={file1: {("I001", "unsorted-imports"): 1}})

    summary = stats.format_summary()

    assert "Fixed 1 issue:" in summary  # Not "issues"


def test_unsafe_fixes_not_applied(sample_source_file):
    """Test that UNSAFE fixes are not applied by default."""
    applier = FixApplier()

    edit = TextEdit(
        rule_id="W008",
        rule_name="unsafe-rule",
        start_line=7,
        start_col=12,
        end_line=7,
        end_col=23,
        replacement="Unsafe change",
    )
    fix = Fix(edits=[edit], message="Unsafe fix", applicability=FixApplicability.UNSAFE)

    applier.apply_fixes(sample_source_file, [fix])

    assert applier.fix_stats.total_fixes == 0
    assert sample_source_file.modified is False
    assert "Unsafe change" not in sample_source_file.source_lines[6]
    assert applier.fix_stats.by_file == {}


def test_unsafe_fixes_applied_when_allowed(sample_source_file):
    """Test that UNSAFE fixes are applied when allow_unsafe=True."""
    applier = FixApplier()
    sample_source_file.config.linter.unsafe_fixes = True

    edit = TextEdit(
        rule_id="W008",
        rule_name="unsafe-rule",
        start_line=7,
        start_col=12,
        end_line=7,
        end_col=23,
        replacement="Unsafe change",
    )
    fix = Fix(edits=[edit], message="Unsafe fix", applicability=FixApplicability.UNSAFE)

    applier.apply_fixes(sample_source_file, [fix])

    assert applier.fix_stats.total_fixes == 0
    assert sample_source_file.modified is True
    assert "Unsafe change" in sample_source_file.source_lines[6]
    assert applier.fix_stats.by_file[sample_source_file.path][("W008", "unsafe-rule")] == 1


def test_diff_mode_does_not_modify_file(sample_source_file):
    """Test that diff mode shows changes but doesn't modify the file."""
    # Mock config with diff enabled
    sample_source_file.config.linter.diff = True
    sample_source_file.config.linter.fix = True

    original_content = sample_source_file.source_lines.copy()
    sample_source_file._original_source_lines = original_content  # noqa: SLF001

    applier = FixApplier()
    edit = TextEdit(
        rule_id="W001",
        rule_name="test-rule",
        start_line=8,
        start_col=12,
        end_line=8,
        end_col=23,
        replacement="Hello Python",
    )
    fix = Fix(edits=[edit], message="Update greeting", applicability=FixApplicability.SAFE)

    applier.apply_fixes(sample_source_file, [fix])

    # Changes should be applied in memory
    assert applier.fix_stats.total_fixes == 0
    assert sample_source_file.modified is True
    assert "Hello Python" in sample_source_file.source_lines[7]

    # But original should be preserved
    assert "Hello World" in sample_source_file.original_source_lines[7]
    assert sample_source_file.original_source_lines == original_content


def test_edit_kind(sample_source_file):
    applier = FixApplier()

    replace_range = Range(start=Position(line=3, character=12), end=Position(line=3, character=23))
    remove_range = Range(start=Position(line=4, character=1), end=Position(line=4, character=1000))
    insert_range = Range(start=Position(line=5, character=1), end=Position(line=5, character=1))
    fixes = [
        Fix(
            edits=[
                TextEdit.replace_at_range(
                    rule_id="W001", rule_name="update-library", diag_range=replace_range, replacement="Replaced"
                ),
                TextEdit.remove_at_range(rule_id="W001", rule_name="update-library", diag_range=remove_range),
            ],
            message="Range helpers",
            applicability=FixApplicability.SAFE,
        ),
        Fix(
            edits=[
                TextEdit.insert_at_range(
                    rule_id="W001", rule_name="update-library", diag_range=insert_range, replacement="Library    Name\n"
                )
            ],
            message="Range helpers",
            applicability=FixApplicability.SAFE,
        ),
    ]

    applier.apply_fixes(sample_source_file, fixes)

    assert applier.fix_stats.total_fixes == 0
    assert "Replaced" in sample_source_file.source_lines[2]
    assert "String" not in sample_source_file.source_lines[3]
    assert "Name" in sample_source_file.source_lines[3]
    assert applier.fix_stats.by_file[sample_source_file.path][("W001", "update-library")] == 3

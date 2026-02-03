"""Integration tests for cache functionality using check_files entrypoint."""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from textwrap import dedent

import msgpack

from robocop.run import check_files, format_files
from tests import working_directory

TEST_DATA = Path(__file__).parent / "test_data" / "integration"


def prepare_test_files(tmp_path: Path) -> Path:
    """
    Copy test files to temporary directory.

    Returns:
        Path to the test robot file.

    """
    config = TEST_DATA / "pyproject.toml"
    test_file = TEST_DATA / "test.robot"
    shutil.copy(config, tmp_path / "pyproject.toml")
    shutil.copy2(test_file, tmp_path / "test.robot")
    return tmp_path / "test.robot"


def get_cache_data(tmp_path: Path) -> dict:
    """
    Load and return cache data.

    Returns:
        Dictionary containing cache data, or empty dict if cache doesn't exist.

    """
    cache_file = tmp_path / ".robocop_cache" / "cache.msgpack"
    if not cache_file.exists():
        return {}
    return msgpack.unpackb(cache_file.read_bytes(), raw=False, strict_map_key=False)


def is_file_in_cache(tmp_path: Path, file_path: Path) -> bool:
    """
    Check if a file is in the cache.

    Returns:
        True if file is cached, False otherwise.

    """
    cache_data = get_cache_data(tmp_path)
    return str(file_path.resolve()) in cache_data.get("linter", {})


class TestCacheIntegration:
    """Integration tests for cache using real check_files entrypoint."""

    def test_cache_hit_file_unchanged(self, tmp_path, capsys):
        """Test that cache is used when file hasn't changed (should see verbose message)."""
        # Arrange - setup files and run initial check to populate cache
        test_file = prepare_test_files(tmp_path)

        with working_directory(tmp_path):
            # First run - populates cache
            first_result = check_files(return_result=True, verbose=True)
            first_count = len(first_result)
            assert first_count > 0, "Should find some issues"

            # Verify cache was created
            assert is_file_in_cache(tmp_path, test_file)
            out1, _ = capsys.readouterr()
            assert "Scanning file:" in out1  # File was scanned

            # Act - run again without modifying file
            second_result = check_files(return_result=True, verbose=True)
            out2, _ = capsys.readouterr()

            # Assert - cache should be used
            assert len(second_result) == first_count, "Results should match from cache"
            assert "Used cached results for 1 of 1 files" in out2

    def test_cache_invalidated_on_file_modification(self, tmp_path, capsys):
        """Test that cache is invalidated when file is modified."""
        # Arrange - setup and populate cache
        test_file = prepare_test_files(tmp_path)

        with working_directory(tmp_path):
            # First run - populates cache
            first_result = check_files(return_result=True, verbose=True)
            first_count = len(first_result)
            assert first_count > 0
            _out1, _ = capsys.readouterr()

            # Modify the file (add a new test case without docs)
            time.sleep(0.01)  # Ensure mtime changes
            test_file.write_text(
                test_file.read_text() + "\n\nNew Test Without Docs\n    Log    New test\n",
                encoding="utf-8",
            )

            # Act - run again with modified file
            second_result = check_files(return_result=True, verbose=True)
            out2, _ = capsys.readouterr()

            # Assert - file should be rescanned (cache invalidated)
            assert "Scanning file:" in out2
            # Should NOT show cached results message since file was rescanned
            assert "Used cached results" not in out2 or "0 of 1" in out2
            # New test case should add another missing doc issue
            assert len(second_result) > first_count

    def test_cache_invalidated_on_config_change(self, tmp_path, capsys):
        """Test that cache is invalidated when linter config changes."""
        # Arrange - setup and populate cache
        prepare_test_files(tmp_path)

        with working_directory(tmp_path):
            # First run with 0201 rule (missing-doc-test-case)
            first_result = check_files(return_result=True, verbose=True)
            assert len(first_result) > 0
            _out1, _ = capsys.readouterr()

            # Act - run with different rules
            second_result = check_files(select=["0701"], return_result=True, verbose=True)
            out2, _ = capsys.readouterr()

            # Assert - should rescan because config changed
            assert "Scanning file:" in out2
            # Results will differ because different rules are selected
            assert len(first_result) != len(second_result) or len(first_result) == 0

    def test_cache_disabled_with_no_cache_flag(self, tmp_path, capsys):
        """Test that cache is bypassed when --no-cache is used."""
        # Arrange - setup and populate cache
        prepare_test_files(tmp_path)

        with working_directory(tmp_path):
            # First run with cache enabled
            first_result = check_files(return_result=True, verbose=True)
            first_count = len(first_result)
            _out1, _ = capsys.readouterr()

            # Act - run with --no-cache flag
            second_result = check_files(cache=False, return_result=True, verbose=True)
            out2, _ = capsys.readouterr()

            # Assert - should rescan even though file unchanged
            assert "Scanning file:" in out2
            assert len(second_result) == first_count
            # Should NOT show cache usage message
            assert "Used cached results" not in out2

    def test_cache_persists_across_runs(self, tmp_path):
        """Test that cache persists and is reused across separate runs."""
        # Arrange
        test_file = prepare_test_files(tmp_path)
        cache_dir = tmp_path / ".robocop_cache"

        with working_directory(tmp_path):
            # First run - creates cache
            first_result = check_files(return_result=True)
            assert cache_dir.exists(), "Cache directory should be created"
            assert (cache_dir / "cache.msgpack").exists(), "Cache file should be created"

            # Verify cache contains data
            cache_data = get_cache_data(tmp_path)
            assert str(test_file.resolve()) in cache_data["linter"], "File should be in cache"

            # Act - second run should use cached data
            second_result = check_files(return_result=True)

            # Assert - results should match
            assert len(second_result) == len(first_result)

    def test_cache_invalidated_on_size_change(self, tmp_path, capsys):
        """Test that cache is invalidated when only file size changes."""
        # Arrange
        test_file = prepare_test_files(tmp_path)

        with working_directory(tmp_path):
            # First run
            check_files(return_result=True, verbose=True)
            _out1, _ = capsys.readouterr()

            # Change file size by adding a comment
            time.sleep(0.01)
            test_file.write_text(test_file.read_text() + "\n# Comment\n", encoding="utf-8")

            # Act
            check_files(return_result=True, verbose=True)
            out2, _ = capsys.readouterr()

            # Assert - should reprocess file
            assert "Scanning file:" in out2

    def test_clear_cache_flag(self, tmp_path, capsys):
        """Test that --clear-cache forces reprocessing of all files."""
        # Arrange - populate cache
        prepare_test_files(tmp_path)

        with working_directory(tmp_path):
            # First run - creates cache
            first_result = check_files(return_result=True, verbose=True)
            cache_dir = tmp_path / ".robocop_cache"
            assert cache_dir.exists()
            _out1, _ = capsys.readouterr()

            # Act - run with --clear-cache
            second_result = check_files(clear_cache=True, return_result=True, verbose=True)
            out2, _ = capsys.readouterr()

            # Assert - should rescan (cache was cleared)
            assert "Scanning file:" in out2
            assert len(second_result) == len(first_result)

    def test_cache_with_multiple_files(self, tmp_path, capsys):
        """Test cache behavior with multiple files."""
        # Arrange - create multiple test files
        test_file = prepare_test_files(tmp_path)
        file2 = tmp_path / "test2.robot"
        shutil.copy2(test_file, file2)

        with working_directory(tmp_path):
            # First run - cache both files
            first_result = check_files(return_result=True, verbose=True)
            first_count = len(first_result)
            out1, _ = capsys.readouterr()
            # Both files should be scanned
            assert out1.count("Scanning file:") == 2

            # Modify only one file
            time.sleep(0.01)
            file2.write_text(file2.read_text() + "\n# Comment\n", encoding="utf-8")

            # Act - run again
            second_result = check_files(return_result=True, verbose=True)
            out2, _ = capsys.readouterr()

            # Assert - only modified file should be scanned
            # One file from cache, one rescanned
            assert "Used cached results for 1 of 2 files" in out2
            assert len(second_result) == first_count  # Results unchanged (just added comment)

    def test_cache_with_fixable_rule(self, tmp_path, capsys):
        """Test cache behavior with fixable rules."""
        # Arrange - create tedt file for fixable rule
        test_file = tmp_path / "test.robot"
        content = dedent("""
        *** Settings ***
        Suite Setup    With Trailing Whitespace    
        """).lstrip()  # noqa: W291
        test_file.write_text(content, encoding="utf-8")

        with working_directory(tmp_path):
            # Act - first run to populate cache
            result1 = check_files(return_result=True, verbose=True)
            out1, _ = capsys.readouterr()
            # Act - second run to regain fixable rules
            result2 = check_files(return_result=True, verbose=True)
            out2, _ = capsys.readouterr()
            # Act - third run that shows fix diff
            result3 = check_files(return_result=True, verbose=True, diff=True)
            out3, _ = capsys.readouterr()
            # Act - fourth run that has all issues (diff does not change it)
            result4 = check_files(return_result=True, verbose=True)
            out4, _ = capsys.readouterr()
            # Act - fifth run that fixes the issue
            result5 = check_files(return_result=True, verbose=True, fix=True)
            out5, _ = capsys.readouterr()
            # Act - sixth run that has only remaining issues
            result6 = check_files(return_result=True, verbose=True)
            out6, _ = capsys.readouterr()

            # Assert - first run not yet cached, all issues
            assert "Used cached results" not in out1
            assert len(result1) == 3
            assert "1 fixable with the ``--fix`` option." in out1

            # Assert - second run cached, all issues
            assert "Used cached results" in out2
            assert len(result2) == 3
            assert "1 fixable with the ``--fix`` option." in out2

            # Assert - third run not cached, only unfixable issues in results (fixable goes to diff)
            assert "Used cached results" not in out3  # we didn't use cache since we generated diff
            assert len(result3) == 2
            assert "Found 3 issues (1 fixed, 2 remaining)." in out3  # it is printed but not applied (diff)

            # Assert - fourth run cached, all issues (no changes from diff)
            assert "Used cached results" in out4
            assert len(result4) == 3
            assert "1 fixable with the ``--fix`` option." in out4

            # Assert - fifth run not cached, only unfixable issues in results (fixable are fixed)
            assert "Used cached results" not in out5
            assert len(result5) == 2
            assert "Found 3 issues (1 fixed, 2 remaining)." in out5

            # Assert - sixth run cached, only unfixable issues (fixable were fixed)
            assert "Used cached results" in out6
            assert len(result6) == 2
            assert "Found 2 issues." in out6

    def test_file_with_parse_error_not_cached(self, tmp_path, capsys):
        """Test that files with parse errors are not cached."""
        # Arrange - create file with actual encoding/binary issues that cause DataError
        test_file = tmp_path / "invalid.robot"
        # Write binary data that's not valid UTF-8 to cause decode error
        test_file.write_bytes(b"\xff\xfe*** Test Cases ***\nInvalid UTF-8: \x80\x81\x82\n")

        with working_directory(tmp_path):
            # First run - should fail to decode
            check_files(return_result=True, verbose=True)
            out1, _ = capsys.readouterr()
            # Should report decode error and skip file
            assert "Failed to decode" in out1

            # File should NOT be in cache (because it failed to parse)
            assert not is_file_in_cache(tmp_path, test_file)

            # Fix the file with valid UTF-8
            time.sleep(0.01)
            test_file.write_text("*** Test Cases ***\nTest\n    Log    Fixed\n", encoding="utf-8")

            # Act - run again with fixed file
            check_files(return_result=True, verbose=True)
            out2, _ = capsys.readouterr()

            # Should process the fixed file
            assert "Scanning file:" in out2
            # Now it should be cached
            assert is_file_in_cache(tmp_path, test_file)

    def test_language_change_invalidates_cache(self, tmp_path, capsys):
        """Test that changing language configuration invalidates cache."""
        # Arrange
        prepare_test_files(tmp_path)

        with working_directory(tmp_path):
            # First run with default language
            first_result = check_files(return_result=True, verbose=True)
            assert len(first_result) > 0
            _out1, _ = capsys.readouterr()

            # Act - run with different language setting
            # Note: language affects the cache key via _compute_cache_key
            check_files(language=["en"], return_result=True, verbose=True)
            out2, _ = capsys.readouterr()

            # Assert - should rescan due to language change
            assert "Scanning file:" in out2

    def test_formatter_file_needs_formatting_then_cached(self, tmp_path, capsys):
        """Test formatter: file needs formatting, gets formatted, then uses cache."""
        # Arrange - create file that needs formatting (bad spacing)
        test_file = tmp_path / "bad_format.robot"
        test_file.write_text("***Test Cases***\nTest\n    Log    Hello\n", encoding="utf-8")

        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("[tool.robocop]\ncache = true\n", encoding="utf-8")

        with working_directory(tmp_path):
            # First run - should format the file
            _ = format_files(check=True, return_result=True, verbose=True)
            out1, _ = capsys.readouterr()
            assert "Formatting" in out1

            # Verify cache shows needs_formatting=False after formatting
            cache_data = get_cache_data(tmp_path)
            if str(test_file.resolve()) in cache_data.get("formatter", {}):
                entry_data = cache_data["formatter"][str(test_file.resolve())]
                # After formatting attempt, should be cached as not needing formatting
                # (either it was formatted or was already correctly formatted)
                assert "needs_formatting" in entry_data

            # Act - run again without modifying file
            _ = format_files(check=True, return_result=True, verbose=True)
            out2, _ = capsys.readouterr()

            # Assert - should use cache (skip formatting)
            assert "Skipped" in out2 or "unchanged" in out2.lower()

    def test_empty_file_integration(self, tmp_path, capsys):
        """Test integration with empty Robot Framework file."""
        # Arrange - create empty file
        test_file = tmp_path / "empty.robot"
        test_file.write_text("", encoding="utf-8")

        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("[tool.robocop]\ncache = true\n", encoding="utf-8")

        with working_directory(tmp_path):
            # First run on empty file
            check_files(return_result=True, verbose=True)
            capsys.readouterr()

            # Verify file is cached (even if empty)
            assert is_file_in_cache(tmp_path, test_file)

            # Add content
            time.sleep(0.01)
            test_file.write_text("*** Test Cases ***\nTest\n    Log    Content added\n", encoding="utf-8")

            # Act - run again
            _ = check_files(return_result=True, verbose=True)
            out2, _ = capsys.readouterr()

            # Assert - should rescan (cache invalidated due to size change)
            assert "Scanning file:" in out2

    def test_default_cli_does_not_override_config_file_disabled(self, tmp_path, capsys):
        """Test CLI without any option set does not override the config file with cache=false."""
        # Arrange - create config file with cache disabled
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("[tool.robocop]\ncache = false\n", encoding="utf-8")
        test_file = tmp_path / "test.robot"
        test_file.write_text("*** Test Cases ***\nTest\n    Log    Hello\n", encoding="utf-8")

        with working_directory(tmp_path):
            # Act - run with default CLI (cache disabled from config)
            check_files(verbose=True, return_result=True)
            out, _ = capsys.readouterr()

            # Assert - should NOT use cache (rescans file)
            assert "Scanning file:" in out
            assert "Used cached results" not in out

            # Assert - cache file should not be created
            cache_dir = tmp_path / ".robocop_cache"
            assert not cache_dir.exists()

    def test_cli_cache_dir_overrides_config_file_disabled(self, tmp_path, capsys):
        """Test CLI --cache-dir does not enable cache and overrides the config file with cache=false."""
        # Arrange - create config file with cache disabled
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("[tool.robocop]\ncache = false\n", encoding="utf-8")
        test_file = tmp_path / "test.robot"
        test_file.write_text("*** Test Cases ***\nTest\n    Log    Hello\n", encoding="utf-8")

        custom_cache_dir = tmp_path / "my_cache"

        with working_directory(tmp_path):
            # Act - run with custom cache_dir via CLI
            # When cache_dir is explicitly set, it should not enable cache and override config file's cache=false
            check_files(cache_dir=custom_cache_dir, return_result=True)

            out, _ = capsys.readouterr()

            # Assert - should NOT use cache (rescans file)
            assert "Used cached results" not in out

    def test_cli_no_cache_flag_overrides_config_file_enabled(self, tmp_path, capsys):
        """Test CLI --no-cache disables cache when config file enables it."""
        # Arrange - create config file with cache enabled
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("[tool.robocop]\ncache = true\n", encoding="utf-8")
        test_file = tmp_path / "test.robot"
        test_file.write_text("*** Test Cases ***\nTest\n    Log    Hello\n", encoding="utf-8")

        with working_directory(tmp_path):
            # First run with default (cache enabled from config)
            check_files(return_result=True, verbose=True)
            _out1, _ = capsys.readouterr()

            # Verify cache was created
            assert is_file_in_cache(tmp_path, test_file)

            # Act - Override config file's cache=true with --no-cache flag
            check_files(cache=False, return_result=True, verbose=True)
            out2, _ = capsys.readouterr()

            # Assert - should NOT use cache (rescans file)
            assert "Scanning file:" in out2
            assert "Used cached results" not in out2

    def test_gitignore_created_in_cache_directory(self, tmp_path):
        """Test that .gitignore file is created in cache directory."""
        # Arrange
        prepare_test_files(tmp_path)

        with working_directory(tmp_path):
            # Act - run check which creates cache
            check_files(return_result=True)

            # Assert - .gitignore should be created
            cache_dir = tmp_path / ".robocop_cache"
            gitignore_file = cache_dir / ".gitignore"
            assert gitignore_file.exists(), ".gitignore should be created in cache directory"
            assert gitignore_file.read_text(encoding="utf-8") == "*\n", ".gitignore should contain '*'"

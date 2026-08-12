import textwrap
from unittest.mock import MagicMock, patch

from robocop.run import print_resource_documentation


class TestDescribeRule:
    def test_describe_rule(self, loaded_linter, capsys):
        with patch("robocop.run.RobocopLinter", MagicMock(return_value=loaded_linter)):
            print_resource_documentation("duplicated-keyword")
        out, _ = capsys.readouterr()
        expected = textwrap.dedent("""
        Rule: duplicated-keyword (DUP02)
        Message: Multiple keywords with name '{name}' (first occurrence in line {first_occurrence_line})
        Severity: E

        Multiple keywords with the same name in the file.

        Do not define keywords with the same name inside the same file. Name matching is case-insensitive and
        ignores spaces and underscore characters.

        Incorrect code example:

            *** Keywords ***
            Keyword
                No Operation

            keyword
                No Operation

            K_eywor d
                No Operation


        """).lstrip()
        assert expected == out

    def test_describe_rule_with_configurables(self, capsys):
        from robocop.linter.rules.lengths import LineTooLongRule  # noqa: PLC0415

        rule = LineTooLongRule()
        mock_resolved_config = MagicMock()
        mock_resolved_config.rules = {"line-too-long": rule}

        with patch("robocop.run.ConfigResolver") as mock_resolver:
            mock_resolver.return_value.resolve_config.return_value = mock_resolved_config
            print_resource_documentation("line-too-long")
        out, _ = capsys.readouterr()
        expected = textwrap.dedent(r"""
        Rule: line-too-long (LEN08)
        Message: Line is too long ({line_length}/{allowed_length})
        Severity: W

        The line is too long.

        Comments with disabler directives (such as ``# robocop: off``) are ignored. Lines that contain URLs are also
        ignored.

        It is possible to ignore lines that match the regex pattern. Configure it using the following option:

            robocop check --configure line-too-long.ignore_pattern=pattern


        Configurables:
            severity_threshold = None
                type: severity_threshold
            line_length = 120
                type: int
                info: number of characters allowed in line
            ignore_pattern = None
                type: pattern_type
                info: ignore lines that contain configured pattern

        """).lstrip()
        assert expected == out

    def test_describe_rule_with_configurables_modified(self, capsys):
        from robocop.linter.rules.lengths import LineTooLongRule  # noqa: PLC0415

        rule = LineTooLongRule()
        rule.configure("line_length", "200")
        rule.configure("severity_threshold", "warning=100:error=150")

        mock_resolved_config = MagicMock()
        mock_resolved_config.rules = {"line-too-long": rule}

        with patch("robocop.run.ConfigResolver") as mock_resolver:
            mock_resolver.return_value.resolve_config.return_value = mock_resolved_config
            print_resource_documentation("line-too-long")
        out, _ = capsys.readouterr()
        expected = textwrap.dedent(r"""
        Rule: line-too-long (LEN08)
        Message: Line is too long ({line_length}/{allowed_length})
        Severity: W

        The line is too long.

        Comments with disabler directives (such as ``# robocop: off``) are ignored. Lines that contain URLs are also
        ignored.

        It is possible to ignore lines that match the regex pattern. Configure it using the following option:

            robocop check --configure line-too-long.ignore_pattern=pattern


        Configurables:
            severity_threshold = E=150:W=100
                type: severity_threshold
            line_length = 200* (default: 120)
                type: int
                info: number of characters allowed in line
            ignore_pattern = None
                type: pattern_type
                info: ignore lines that contain configured pattern

        """).lstrip()
        assert expected == out

import textwrap
from unittest.mock import MagicMock, patch

from robocop.cli import describe_rule

from tests.linter.cli.conftest import loaded_linter


class TestDescribeRule:
    def test_describe_rule(self, loaded_linter, capsys):
        with patch("robocop.cli.RobocopLinter", MagicMock(return_value=loaded_linter)):
            describe_rule("duplicated-keyword")
        out, _ = capsys.readouterr()
        expected = textwrap.dedent("""
        Rule: duplicated-keyword (0802)
        Message: Multiple keywords with name '{{ name }}' (first occurrence in line {{ first_occurrence_line }})
        Severity: E

        Do not define keywords with the same name inside the same file. Name matching is case-insensitive and
        ignores spaces and underscore characters.
        Duplicated keyword names example::

            *** Keywords ***
            Keyword
                No Operation
    
            keyword
                No Operation
    
            K_eywor d
                No Operation


        """).lstrip()
        assert expected == out

    def test_describe_rule_with_configurables(self, loaded_linter, capsys):
        with patch("robocop.cli.RobocopLinter", MagicMock(return_value=loaded_linter)):
            describe_rule("line-too-long")
        out, _ = capsys.readouterr()
        expected = textwrap.dedent("""
        Rule: line-too-long (0508)
        Message: Line is too long ({{ line_length }}/{{ allowed_length }})
        Severity: W

        It is possible to ignore lines that match regex pattern. Configure it using following option::
        
            robocop --configure line-too-long:ignore_pattern:pattern
        
        The default pattern is ``https?://\\S+`` that ignores the lines that look like an URL.
        
        
        Configurables:
            line_length = 120
                type: int
                info: number of characters allowed in line
            ignore_pattern = re.compile('https?://\\\\S+')
                type: pattern_type
                info: ignore lines that contain configured pattern
            severity_threshold

        """).lstrip()
        assert expected == out

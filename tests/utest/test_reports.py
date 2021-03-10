import pytest
from robocop.reports import JsonReport, FileStatsReport
from robocop.rules import Message, Rule, RuleSeverity


@pytest.fixture
def message():
    msg = (
        "some-message",
        "Some description",
        RuleSeverity.WARNING,
        ('param_name', 'param_priv_name', int)
    )
    return Rule('0101', msg)


class TestReports:
    def test_json_report(self, message):
        report = JsonReport()
        issue = Message(rule=message, source='some/path/file.robot', node=None, lineno=50, col=10)
        report.add_message(issue)
        assert report.issues[0] == {
            'source': 'some/path/file.robot',
            'column': 10,
            'line': 50,
            'rule_id': '0101',
            'rule_name': 'some-message',
            'severity': 'W',
            'description': 'Some description'
        }

    @pytest.mark.parametrize('files, files_with_issues, output', [
        (0, 0, 'No files were processed'),
        (10, 0, 'Processed 10 file(s) but no issues were found'),
        (10, 6, 'Processed 10 file(s) from which 6 file(s) contained issues')
    ])
    def test_file_stats_report(self, files, files_with_issues, output, message):
        report = FileStatsReport()
        report.files_count = files
        report.files_with_issues = files_with_issues
        issue = Message(rule=message, source='some/path/file.robot', node=None, lineno=50, col=10)
        report.add_message(issue)
        assert report.get_report() == output

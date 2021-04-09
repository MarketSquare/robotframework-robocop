from pathlib import Path

import pytest
from robot.api import get_model

import robocop
from robocop.rules import Message, RuleSeverity, Rule
from robocop.utils import issues_to_lsp_diagnostic
from robocop.exceptions import InvalidArgumentError


@pytest.fixture
def rule():
    msg = (
        "some-message",
        "Some description",
        RuleSeverity.WARNING,
        ('param_name', 'param_priv_name', int)
    )
    return Rule('0101', msg)


class TestAPI:
    def test_run_check_in_memory(self):
        config = robocop.Config(root='.')

        robocop_runner = robocop.Robocop(config=config)
        robocop_runner.reload_config()
        in_memory = "*** Settings ***\n\n"
        ast_model = get_model(in_memory)
        issues = robocop_runner.run_check(ast_model, r'C:\directory\file.robot', in_memory)
        expected_issues = {
            'Missing documentation in suite',
            'Section is empty',            
            'Too many blank lines at the end of file'
        }
        actual_issues = {issue.desc for issue in issues}
        assert expected_issues == actual_issues

    def test_run_check_in_memory_with_windows_line_endings(self):
        config = robocop.Config(root='.')

        robocop_runner = robocop.Robocop(config=config)
        robocop_runner.reload_config()
        in_memory = "*** Settings *** \r\n\r\n"
        ast_model = get_model(in_memory)
        issues = robocop_runner.run_check(ast_model, r'C:\directory\file.robot', in_memory)
        expected_issues = {
            'Missing documentation in suite',
            'Section is empty',
            'Trailing whitespace at the end of line',
            'Too many blank lines at the end of file'
        }
        assert all(issue.desc in expected_issues for issue in issues)

    def test_run_check_in_memory_with_mac_line_endings(self):
        config = robocop.Config(root='.')

        robocop_runner = robocop.Robocop(config=config)
        robocop_runner.reload_config()
        in_memory = "*** Settings *** \r\r"
        ast_model = get_model(in_memory)
        issues = robocop_runner.run_check(ast_model, r'C:\directory\file.robot', in_memory)
        expected_issues = {
            'Missing documentation in suite',
            'Section is empty',
            'Trailing whitespace at the end of line',
            'Too many blank lines at the end of file'
        }
        actual_issues = {issue.desc for issue in issues}
        assert expected_issues == actual_issues

    def test_run_check_in_memory_with_config(self):
        config_path = Path(Path(__file__).parent.parent, 'test_data', 'api_config')
        config = robocop.Config(root=config_path)

        robocop_runner = robocop.Robocop(config=config)
        robocop_runner.reload_config()
        in_memory = "*** Settings ***\n\n"
        ast_model = get_model(in_memory)
        issues = robocop_runner.run_check(ast_model, r'C:\directory\file.robot', in_memory)
        issues_by_desc = [issue.desc for issue in issues]
        assert 'Missing documentation in suite' in issues_by_desc
        assert 'Section is empty' not in issues_by_desc

    def test_invalid_config(self):
        config_path = Path(Path(__file__).parent.parent, 'test_data', 'api_invalid_config')
        config = robocop.Config(root=config_path)

        with pytest.raises(InvalidArgumentError) as exception:
            robocop.Robocop(config=config)
        assert r'Invalid configuration for Robocop:\nunrecognized arguments: --some' in str(exception)

    def test_lsp_diagnostic(self, rule):
        issues = [
            Message(
                rule=rule,
                source=r'C:\directory\file.robot',
                node=None, lineno=10, col=10, end_lineno=11, end_col=50
            ),
            Message(
                rule=rule,
                source=r'C:\directory\file.robot',
                node=None, lineno=1, col=1, end_lineno=None, end_col=None
            )
        ]
        expected_diagnostic = [
            {
                'range': {
                    'start': {
                        'line': 9,
                        'character': 10
                    },
                    'end': {
                        'line': 10,
                        'character': 50
                    }
                },
                'severity': 2,
                'code': '0101',
                'source': 'robocop',
                'message': 'Some description'
            },
            {
                'range': {
                    'start': {
                        'line': 0,
                        'character': 1
                    },
                    'end': {
                        'line': 0,
                        'character': 1
                    }
                },
                'severity': 2,
                'code': '0101',
                'source': 'robocop',
                'message': 'Some description'
            }
        ]
        diagnostic = issues_to_lsp_diagnostic(issues)
        assert diagnostic == expected_diagnostic

    def test_ignore_sys_argv(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["robocorp", "--some", "args.robot"])
        config = robocop.Config()
        robocop_runner = robocop.Robocop(config=config)
        robocop_runner.reload_config()
        in_memory = "*** Settings ***\n\n"
        ast_model = get_model(in_memory)
        issues = robocop_runner.run_check(ast_model, r'C:\directory\file.robot', in_memory)
        expected_issues = {
            'Missing documentation in suite',
            'Section is empty',
            'Too many blank lines at the end of file'
        }
        assert all(issue.desc in expected_issues for issue in issues)

    def test_robocop_api_no_trailing_blank_line_message(self):
        """ Bug from #307 """
        source = "*** Test Cases ***\nTest\n    Fail\n    \nTest\n    Fail\n"
        ast = get_model(source)

        config = robocop.Config()
        robocop_runner = robocop.Robocop(config=config)
        robocop_runner.reload_config()

        issues = robocop_runner.run_check(ast, 'target.robot', source)
        diag_issues = issues_to_lsp_diagnostic(issues)
        assert all(d["message"] != "Missing trailing blank line at the end of file" for d in diag_issues)

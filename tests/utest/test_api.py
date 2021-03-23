import pytest
from robot.api import get_model

import robocop
from robocop.rules import Message, RuleSeverity, Rule
from robocop.utils import issues_to_lsp_diagnostic


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
            'Section is empty'
        }
        assert all(issue.desc in expected_issues for issue in issues)

    def test_lsp_diagnostic(self, rule):
        issues = [
            Message(rule=rule, source=r'C:\directory\file.robot', node=None, lineno=10, col=10),
            Message(rule=rule, source=r'C:\directory\file.robot', node=None, lineno=1, col=1)
        ]
        expected_diagnostic = [
            {
                'range': {
                    'start': {
                        'line': 9,
                        'character': 10
                    },
                    'end': {
                        'line': 9,
                        'character': 10
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

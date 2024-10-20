import ast

import pytest

import robocop.exceptions
from robocop.rules import Rule, RuleParam, RuleSeverity


@pytest.fixture
def valid_msg():
    return Rule(rule_id="0101", name="some-message", msg="Some description", severity=RuleSeverity.WARNING)


@pytest.fixture
def valid_msg_with_conf():
    return Rule(
        RuleParam(name="param_name", converter=int, default=1, desc=""),
        rule_id="0101",
        name="some-message",
        msg="Some description",
        severity=RuleSeverity.WARNING,
    )


INVALID_MSG_MISSING_SEVERITY = (
    "some-message",
    "Some description",
)


INVALID_MSG_MISSING_DESC_SEV = "some-message"


class TestMessage:
    def test_get_fullname(self, valid_msg):  # noqa
        msg = valid_msg.prepare_message(
            source=None,
            node=None,
            lineno=None,
            col=None,
            end_lineno=None,
            end_col=None,
            extended_disablers=None,
            sev_threshold_value=None,
            severity=None,
        )
        assert msg.get_fullname() == "W0101 (some-message)"

    @staticmethod
    def change_severity(msg, severity):
        msg.configure("severity", severity)
        return msg

    @pytest.mark.parametrize(
        "severity, exp_sev",
        [
            ("e", "E"),
            ("error", "E"),
            ("i", "I"),
            ("info", "I"),
            ("w", "W"),
            ("warning", "W"),
            ("eRROr", "E"),
            ("Warning", "W"),
        ],
    )
    def test_change_message_severity(self, valid_msg, severity, exp_sev):  # noqa
        assert str(TestMessage.change_severity(valid_msg, severity).severity) == exp_sev

    @pytest.mark.parametrize("severity", ["invalid", 1, "errorE", None, {}])
    def test_change_message_severity_invalid(self, valid_msg, severity):  # noqa
        with pytest.raises(robocop.exceptions.RuleParamFailedInitError) as err:
            valid_msg.configure("severity", severity)
        assert (
            f"Failed to configure param `severity` with value `{severity}`. Received error `Choose one from: I, W, E.`"
            in err.value.args[0]
        )

    def test_get_configurable_existing(self, valid_msg_with_conf):  # noqa
        assert str(valid_msg_with_conf.config["param_name"]) == str(
            RuleParam(name="param_name", converter=int, default=1, desc="")
        )

    def test_parse_invalid_configurable(self):
        with pytest.raises(robocop.exceptions.RuleParamFailedInitError) as err:
            Rule(
                RuleParam(name="Some", default="s", converter=int, desc=""),
                rule_id="0101",
                name="some-message",
                msg="Some description",
                severity=RuleSeverity.WARNING,
            )
        assert (
            rf"Failed to configure param `Some` with value `s`. "
            rf"Received error `invalid literal for int() with base 10: 's'`.\n    Parameter type: <class 'int'>\n"
            in str(err)
        )

    def test_parse_valid_configurable(self):
        rule = Rule(
            RuleParam(name="Some", default="5", converter=int, desc=""),
            rule_id="0101",
            name="some-message",
            msg="Some description",
            severity=RuleSeverity.WARNING,
        )
        assert rule.config["Some"].value == 5

    @pytest.mark.parametrize(
        "source, range, range_exp",
        [
            ("path/to/file1.robot", (None, None, None, None), (10, 1, 10, 1)),
            ("path/to/file1.robot", (15, None, None, 7), (15, 1, 15, 7)),
            ("path/to/file1.robot", (None, 20, 20, None), (10, 20, 20, 20)),
            ("path/to/file2.robot", (15, 200, None, None), (15, 200, 15, 200)),
        ],
    )
    def test_prepare_message(self, valid_msg, source, range, range_exp):  # noqa
        node = ast.AST()
        node.lineno = 10
        lineno, col, end_lineno, end_col = range
        lineno_exp, col_exp, end_lineno_exp, end_col_exp = range_exp
        msg = valid_msg.prepare_message(
            source=source,
            node=node,
            lineno=lineno,
            col=col,
            end_lineno=end_lineno,
            end_col=end_col,
            extended_disablers=None,
            sev_threshold_value=None,
            severity=None,
        )
        assert msg.line == lineno_exp
        assert msg.col == col_exp
        assert msg.end_line == end_lineno_exp
        assert msg.end_col == end_col_exp
        assert msg.source == source

    @pytest.mark.parametrize(
        "kwargs, msg, exp",
        [
            (
                {},
                "Some description {{ string }} and {{ number }}",
                "Some description  and ",
            ),
            (
                {"string": 1, "number": "smth"},
                "Some description {{ string }} and {{ number }}",
                "Some description 1 and smth",
            ),
            (
                {"string": "smth"},
                "Some description {{ string }} and {{ number }}",
                "Some description smth and ",
            ),
            (
                {"number": "smth", "string": 1, "other": 10},
                "Some description {{ string }} and {{ number }}",
                "Some description 1 and smth",
            ),
            (
                {"number": 10},
                "Some description {{ string -}} and {{ number }}",  # -}} means to remove trailing whitespace
                "Some description and 10",
            ),
            (
                {"number": 10, "variable": "smth"},
                "You can supply variables like {{ variable }} or {{ number }}. "
                "Basic {% if number==10 %}jinja {% endif %}syntax supported",
                "You can supply variables like smth or 10. Basic jinja syntax supported",
            ),
            (
                {"number": 11, "variable": "smth"},
                "You can supply variables like {{ variable }} or {{ number }}. "
                "Basic {% if number==10 %}jinja {% endif %}syntax supported",
                "You can supply variables like smth or 11. Basic syntax supported",
            ),
        ],
    )
    def test_prepare_message_with_jinja(self, kwargs, msg, exp):  # noqa
        node = ast.AST()
        node.lineno = 10
        rule = Rule(rule_id="0101", name="some-message", msg=msg, severity=RuleSeverity.WARNING)
        msg = rule.prepare_message(
            source="file1.robot",
            node=node,
            lineno=None,
            col=None,
            end_lineno=None,
            end_col=None,
            extended_disablers=None,
            sev_threshold_value=None,
            severity=None,
            **kwargs,
        )
        assert msg.desc == exp

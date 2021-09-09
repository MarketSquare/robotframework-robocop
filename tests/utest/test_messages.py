import ast
import pytest
from robocop.rules import Rule, RuleSeverity
import robocop.exceptions


@pytest.fixture
def valid_msg():
    msg = ("some-message", "Some description", RuleSeverity.WARNING)
    return Rule("0101", msg)


@pytest.fixture
def valid_msg_with_conf():
    msg = (
        "some-message",
        "Some description",
        RuleSeverity.WARNING,
        ("param_name", "param_priv_name", int),
    )
    return Rule("0101", msg)


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
            ext_disablers=None,
        )
        assert msg.get_fullname() == "W0101 (some-message)"

    @staticmethod
    def change_severity(msg, severity):
        msg.change_severity(severity)
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
        assert TestMessage.change_severity(valid_msg, severity).severity.value == exp_sev

    @pytest.mark.parametrize("severity", ["invalid", 1, "errorE", None, dict()])
    def test_change_message_severity_invalid(self, valid_msg, severity):  # noqa
        with pytest.raises(robocop.exceptions.InvalidRuleSeverityError) as err:
            valid_msg.change_severity(severity)
        assert rf"Fatal error: Tried to configure message some-message with invalid severity: {severity}" in str(err)

    def test_get_configurable_existing(self, valid_msg_with_conf):  # noqa
        assert valid_msg_with_conf.get_configurable("param_name") == (
            "param_name",
            "param_priv_name",
            int,
        )

    def test_get_configurable_empty_configurables(self, valid_msg):  # noqa
        assert valid_msg.get_configurable("param_name") is None

    def test_get_configurable_non_existing(self, valid_msg_with_conf):  # noqa
        assert valid_msg_with_conf.get_configurable("invalid_param") is None

    @pytest.mark.parametrize("msg", [INVALID_MSG_MISSING_SEVERITY, INVALID_MSG_MISSING_DESC_SEV, (), None, 1])
    def test_parse_invalid_body(self, msg):
        with pytest.raises(robocop.exceptions.InvalidRuleBodyError) as err:
            Rule("0101", msg)
        assert rf"Fatal error: Rule '0101' has invalid body:\n{msg}" in str(err)

    @pytest.mark.parametrize(
        "configurable",
        [
            [None],
            [1],
            [()],
            [("some", "some", int, 5, 5)],
            [("some", "some", str), None],
        ],
    )
    def test_parse_invalid_configurable(self, configurable):
        msg = ("some-message", "Some description", RuleSeverity.WARNING)
        body = msg + tuple(configurable)
        with pytest.raises(robocop.exceptions.InvalidRuleConfigurableError) as err:
            Rule("0101", body)
        assert rf"Fatal error: Rule '0101' has invalid configurable:\n{body}" in str(err)

    @pytest.mark.parametrize(
        "configurable",
        [
            [("some", "some", int)],
            [(1, 2, 3)],
            [("some", "some", int), ("some2", "some2", str)],
        ],
    )
    def test_parse_valid_configurable(self, configurable):
        msg = ("some-message", "Some description", RuleSeverity.WARNING)
        body = msg + tuple(configurable)
        rule = Rule("0101", body)
        assert rule.configurable == configurable

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
            ext_disablers=None,
        )
        assert msg.line == lineno_exp
        assert msg.col == col_exp
        assert msg.end_line == end_lineno_exp
        assert msg.end_col == end_col_exp
        assert msg.source == source

    @pytest.mark.parametrize(
        "args, desc, exp_error",
        [
            (
                [],
                "Some description %s and %d",
                "not enough arguments for format string",
            ),
            (
                [1, "smth"],
                "Some description %s and %d",
                "%d format: a number is required, not str",
            ),
            (
                ["smth"],
                "Some description %s and %d",
                "not enough arguments for format string",
            ),
            (
                ["smth", 1, 10],
                "Some description %s and %d",
                "not all arguments converted during string formatting",
            ),
            (
                [10],
                "Some description",
                "not all arguments converted during string formatting",
            ),
        ],
    )
    def test_prepare_invalid_message_invalid_arg(self, valid_msg, args, desc, exp_error):  # noqa
        node = ast.AST()
        node.lineno = 10
        valid_msg.desc = desc
        with pytest.raises(robocop.exceptions.InvalidRuleUsageError) as err:
            valid_msg.prepare_message(
                *args,
                source="file1.robot",
                node=node,
                lineno=None,
                col=None,
                end_lineno=None,
                end_col=None,
                ext_disablers=None,
            )
        assert rf"Fatal error: Rule '0101' failed to prepare message description with error: {exp_error}" in str(err)

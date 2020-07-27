import pytest
import ast
from robocop.messages import Message, MessageSeverity


@pytest.fixture
def valid_msg():
    msg = (
        "some-message",
        "Some description",
        MessageSeverity.WARNING
    )
    return Message('0101', msg)


@pytest.fixture
def valid_msg_with_conf():
    msg = (
        "some-message",
        "Some description",
        MessageSeverity.WARNING,
        ('param_name', 'param_priv_name', int)
    )
    return Message('0101', msg)


invalid_msg_missing_severity = (
    "some-message",
    "Some description",
)


invalid_msg_missing_desc_sev = (
    "some-message"
)


class TestMessage:
    def test_get_fullname(self, valid_msg):
        assert valid_msg.get_fullname() == 'W0101 (some-message)'

    @staticmethod
    def change_severity_and_get_fullname(msg, severity):
        msg.change_severity(severity)
        return msg.get_fullname()

    @pytest.mark.parametrize('severity, expected_severity', [
        ('e', 'E'),
        ('error', 'E'),
        ('i', 'I'),
        ('info', 'I'),
        ('w', 'W'),
        ('warning', 'W'),
        ('f', 'F'),
        ('fatal', 'F'),
        ('eRROr', 'E'),
        ('Warning', 'W')
    ])
    def test_change_message_severity(self, valid_msg, severity, expected_severity):
        assert TestMessage.change_severity_and_get_fullname(valid_msg, severity) == f"{expected_severity}0101 (some-message)"

    @pytest.mark.parametrize('severity', [
        'invalid',
        1,
        'errorE',
        None,
        dict()
    ])
    def test_change_message_severity_invalid(self, valid_msg, capsys, severity):
        with pytest.raises(SystemExit):
            valid_msg.change_severity(severity)
        out, err = capsys.readouterr()
        assert str(err) == f"Fatal error: Tried to configure message some-message with invalid severity: {severity}\n"

    def test_get_configurable_existing(self, valid_msg_with_conf, capsys):
        assert valid_msg_with_conf.get_configurable('param_name') == ('param_name', 'param_priv_name', int)

    def test_get_configurable_empty_configurables(self, valid_msg, capsys):
        assert valid_msg.get_configurable('param_name') is None

    def test_get_configurable_non_existing(self, valid_msg_with_conf, capsys):
        assert valid_msg_with_conf.get_configurable('invalid_param') is None

    @pytest.mark.parametrize('msg', [
        invalid_msg_missing_severity,
        invalid_msg_missing_desc_sev,
        (),
        None,
        1
    ])
    def test_parse_invalid_body(self, capsys, msg):
        with pytest.raises(SystemExit):
            Message('0101', msg)
        out, err = capsys.readouterr()
        assert str(err) == f"Fatal error: Message '0101' has invalid body:\n{msg}\n"

    @pytest.mark.parametrize('configurable', [
        [None],
        [1],
        [()],
        [('some', 'some', int, 5)],
        [('some', 'some', str), None]
    ])
    def test_parse_invalid_configurable(self, capsys, configurable):
        msg = (
            "some-message",
            "Some description",
            MessageSeverity.WARNING
        )
        body = msg + tuple(configurable)
        with pytest.raises(SystemExit):
            Message('0101', body)
        out, err = capsys.readouterr()
        assert str(err) == f"Fatal error: Message '0101' has invalid configurable:\n{body}\n"

    @pytest.mark.parametrize('configurable', [
        [('some', 'some', int)],
        [(1, 2, 3)],
        [('some', 'some', int), ('some2', 'some2', str)]
    ])
    def test_parse_valid_configurable(self, configurable):
        msg = (
            "some-message",
            "Some description",
            MessageSeverity.WARNING
        )
        body = msg + tuple(configurable)
        message = Message('0101', body)
        assert message.configurable == configurable

    @pytest.mark.parametrize('source, lineno, col, lineno_exp, col_exp', [
        ('path/to/file1.robot', None, None, 10, 0),
        ('path/to/file1.robot', 15, None, 15, 0),
        ('path/to/file1.robot', None, 20, 10, 20),
        ('path/to/file2.robot', 15, 200, 15, 200),

    ])
    def test_prepare_message(self, valid_msg, source, lineno, col, lineno_exp, col_exp):
        node = ast.AST()
        node.lineno = 10
        msg = valid_msg.prepare_message(source=source, node=node, lineno=lineno, col=col)
        assert msg.line == lineno_exp
        assert msg.col == col_exp
        assert msg.source == source

    @pytest.mark.parametrize('args, desc, exp_error', [
        ([], "Some description %s and %d", "not enough arguments for format string"),
        ([1, 'smth'], "Some description %s and %d", "%d format: a number is required, not str"),
        (['smth'], "Some description %s and %d", "not enough arguments for format string"),
        (['smth', 1, 10], "Some description %s and %d", "not all arguments converted during string formatting"),
        ([10], "Some description", "not all arguments converted during string formatting"),
    ])
    def test_prepare_invalid_message_invalid_arg(self, capsys, valid_msg, args, desc, exp_error):
        node = ast.AST()
        node.lineno = 10
        valid_msg.desc = desc
        with pytest.raises(SystemExit):
            valid_msg.prepare_message(*args, source='file1.robot', node=node, lineno=None, col=None)
        out, err = capsys.readouterr()
        assert str(err) == f"Fatal error: Message '0101' failed to prepare message description with error:{exp_error}\n"

import pytest
from robocop.run import Robocop
from robocop.checkers import VisitorChecker
from robocop.messages import MessageSeverity


@pytest.fixture
def robocop_instance():
    return Robocop()


class ValidChecker(VisitorChecker):
    msgs = {
        "0101": (
            "some-message",
            "Some description",
            MessageSeverity.WARNING
        )
    }


class CheckerDuplicatedMessageName(VisitorChecker):
    msgs = {
        "0101": (
            "some-message",
            "Some description",
            MessageSeverity.WARNING
        ),
        "0102": (
            "some-message",
            "Some description2",
            MessageSeverity.INFO
        )
    }


class CheckerDuplicatedWithOtherCheckerMessageName(VisitorChecker):
    msgs = {
        "0102": (
            "some-message",
            "Some description",
            MessageSeverity.WARNING
        )
    }


class CheckerDuplicatedWithOtherCheckerMessageId(VisitorChecker):
    msgs = {
        "0101": (
            "some-message2",
            "Some description",
            MessageSeverity.WARNING
        )
    }


class TestCheckerInvalidConf:
    def test_duplicated_message_name_inside_checker(self, capsys, fixture_robocop_instance):
        with pytest.raises(SystemExit):
            robocop_instance.register_checker(CheckerDuplicatedMessageName(fixture_robocop_instance))
        _, err = capsys.readouterr()
        assert str(err) == "Fatal error: Message name 'some-message' defined in CheckerDuplicatedMessageName " \
                           "was already defined in CheckerDuplicatedMessageName\n"

    def test_duplicated_message_name_outside_checker(self, capsys, fixture_robocop_instance):
        robocop_instance.register_checker(ValidChecker(robocop_instance))
        with pytest.raises(SystemExit):
            robocop_instance.register_checker(CheckerDuplicatedWithOtherCheckerMessageName(fixture_robocop_instance))
        _, err = capsys.readouterr()
        assert str(err) == f"Fatal error: Message name 'some-message' defined in " \
                           f"CheckerDuplicatedWithOtherCheckerMessageName was already defined in ValidChecker\n"

    def test_duplicated_message_id_outside_checker(self, capsys, fixture_robocop_instance):
        robocop_instance.register_checker(ValidChecker(robocop_instance))
        with pytest.raises(SystemExit):
            robocop_instance.register_checker(CheckerDuplicatedWithOtherCheckerMessageId(fixture_robocop_instance))
        _, err = capsys.readouterr()
        assert str(err) == f"Fatal error: Message id '0101' defined in " \
                           f"CheckerDuplicatedWithOtherCheckerMessageId was already defined in ValidChecker\n"

import pytest
from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity
import robocop.exceptions


class ValidChecker(VisitorChecker):
    rules = {
        "0101": (
            "some-message",
            "Some description",
            RuleSeverity.WARNING
        )
    }


class CheckerDuplicatedMessageName(VisitorChecker):
    rules = {
        "0101": (
            "some-message",
            "Some description",
            RuleSeverity.WARNING
        ),
        "0102": (
            "some-message",
            "Some description2",
            RuleSeverity.INFO
        )
    }


class CheckerDuplicatedWithOtherCheckerMessageName(VisitorChecker):
    rules = {
        "0102": (
            "some-message",
            "Some description",
            RuleSeverity.WARNING
        )
    }


class CheckerDuplicatedWithOtherCheckerMessageId(VisitorChecker):
    rules = {
        "0101": (
            "some-message2",
            "Some description",
            RuleSeverity.WARNING
        )
    }


class TestCheckerInvalidConf:
    def test_duplicated_message_name_inside_checker(self, robocop_instance):  # noqa
        with pytest.raises(robocop.exceptions.DuplicatedRuleError) as err:
            robocop_instance.register_checker(CheckerDuplicatedMessageName())
        assert "Fatal error: Message name 'some-message' defined in CheckerDuplicatedMessageName " \
               "was already defined in CheckerDuplicatedMessageName" in str(err)

    def test_duplicated_message_name_outside_checker(self, robocop_instance):  # noqa
        robocop_instance.register_checker(ValidChecker())
        with pytest.raises(robocop.exceptions.DuplicatedRuleError) as err:
            robocop_instance.register_checker(CheckerDuplicatedWithOtherCheckerMessageName())
        assert "Fatal error: Message name 'some-message' defined in " \
               "CheckerDuplicatedWithOtherCheckerMessageName was already defined in ValidChecker" in str(err)

    def test_duplicated_message_id_outside_checker(self, robocop_instance):  # noqa
        robocop_instance.register_checker(ValidChecker())
        with pytest.raises(robocop.exceptions.DuplicatedRuleError) as err:
            robocop_instance.register_checker(CheckerDuplicatedWithOtherCheckerMessageId())
        assert "Fatal error: Message id '0101' defined in " \
               "CheckerDuplicatedWithOtherCheckerMessageId was already defined in ValidChecker" in str(err)

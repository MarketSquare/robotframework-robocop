import pytest

import robocop.exceptions
from robocop.checkers import VisitorChecker
from robocop.rules import Rule


class ValidChecker(VisitorChecker):
    reports = ("some-message",)
    # rules are autofilled but we need to do it manually in unit test
    rules = {"some-message": Rule(rule_id="0101", name="some-message", msg="Some description", severity="W")}


class CheckerDuplicatedMessageName(VisitorChecker):
    reports = (
        "some-message",
        "some-message2",
    )
    rules = {
        "some-message": Rule(rule_id="0101", name="some-message", msg="Some description", severity="W"),
        "some-message2": Rule(rule_id="0102", name="some-message2", msg="Some description2", severity="I"),
    }


class CheckerDuplicatedWithOtherCheckerMessageName(VisitorChecker):
    reports = ("some-message",)
    rules = {"some-message": Rule(rule_id="0102", name="some-message", msg="Some description", severity="W")}


class CheckerDuplicatedWithOtherCheckerMessageId(VisitorChecker):
    rules = {"some-message2": Rule(rule_id="0101", name="some-message2", msg="Some description", severity="W")}


class TestCheckerInvalidConf:
    def test_duplicated_message_name_outside_checker(self, robocop_instance):  # noqa
        robocop_instance.register_checker(ValidChecker())
        with pytest.raises(robocop.exceptions.DuplicatedRuleError) as err:
            robocop_instance.register_checker(CheckerDuplicatedWithOtherCheckerMessageName())
        assert (
            "Fatal error: Rule name 'some-message' defined in "
            "CheckerDuplicatedWithOtherCheckerMessageName was already defined in ValidChecker" in str(err)
        )

    def test_duplicated_message_id_outside_checker(self, robocop_instance):  # noqa
        robocop_instance.register_checker(ValidChecker())
        with pytest.raises(robocop.exceptions.DuplicatedRuleError) as err:
            robocop_instance.register_checker(CheckerDuplicatedWithOtherCheckerMessageId())
        assert (
            "Fatal error: Rule id '0101' defined in "
            "CheckerDuplicatedWithOtherCheckerMessageId was already defined in ValidChecker" in str(err)
        )

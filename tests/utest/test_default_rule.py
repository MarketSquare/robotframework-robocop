from robocop import __version__
from robocop.rules import DefaultRule, Rule, RuleSeverity


class TestDefaultRule:
    def test_instance_of_rule(self):
        r = DefaultRule(
            rule_id="0001",
            name="amazing-rule",
            msg="Amazing error message",
            severity=RuleSeverity.WARNING,
        )

        assert isinstance(r, Rule)

    def test_has_help_url(self):
        r = DefaultRule(
            rule_id="0001",
            name="amazing-rule",
            msg="Amazing error message",
            severity=RuleSeverity.WARNING,
        )

        assert r.help_url == f"https://robocop.readthedocs.io/en/{__version__}/rules_list.html#amazing-rule"

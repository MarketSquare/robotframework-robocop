from robocop.linter.rules import Rule, RuleSeverity, VisitorChecker


class PluginRule(Rule):
    """Rule shipped with the example plugin."""

    name = "plugin-rule"
    rule_id = "EXPL01"
    message = "Test case name '{name}' comes from the plugin rule"
    severity = RuleSeverity.INFO
    added_in_version = "9.0.0"


class PluginChecker(VisitorChecker):
    """Checker shipped with the example plugin."""

    plugin_rule: PluginRule

    def visit_TestCaseName(self, node) -> None:  # noqa: N802
        self.report(self.plugin_rule, name=node.name, node=node)

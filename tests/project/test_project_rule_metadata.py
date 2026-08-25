from robocop.linter.rules import ProjectChecker
from robocop.runtime.resolver import LinterImporter


def get_all_rules():
    importer = LinterImporter()
    for checker in importer.get_initialized_checkers():
        for name, rule in checker.rules.items():
            if name == rule.name:
                yield checker, rule


class TestProjectRuleMetadata:
    def test_project_rules_are_reported_by_project_checkers(self):
        for checker, rule in get_all_rules():
            if rule.project_rule:
                assert isinstance(checker, ProjectChecker), (
                    f"Rule {rule.name} is marked as a project rule but {type(checker).__name__} is not a ProjectChecker"
                )

    def test_rules_of_project_checkers_are_marked(self):
        for checker, rule in get_all_rules():
            if isinstance(checker, ProjectChecker):
                assert rule.project_rule, (
                    f"Rule {rule.name} is reported by a ProjectChecker and should set project_rule = True"
                )

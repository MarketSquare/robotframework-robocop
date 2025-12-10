from robocop.config import ConfigManager
from robocop.linter.rules import ProjectChecker, Rule, RuleSeverity


class ProjectCheckerRule(Rule):
    rule_id = "9901"
    name = "project-checker-rule"
    message = "This check will be called after visiting all files"
    severity = RuleSeverity.INFO


class TestTotalCountRule(Rule):
    rule_id = "9902"
    name = "test-total-count"
    message = "There is total of {files} files in the project."
    severity = RuleSeverity.INFO


class MyProjectChecker(ProjectChecker):
    """Project checker."""

    project_checker: ProjectCheckerRule
    test_total_count: TestTotalCountRule

    def scan_project(self, config_manager: ConfigManager) -> None:
        files_count = 0
        for robot_file in config_manager.root.rglob("*.robot"):
            files_count += 1
            self.report(self.project_checker, source=robot_file)
        # files can be also parsed (with get_model) and checked here
        self.report(self.test_total_count, source="Project-name", files=files_count)

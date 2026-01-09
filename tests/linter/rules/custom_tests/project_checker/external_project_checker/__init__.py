from pathlib import Path

from robocop.config_manager import ConfigManager
from robocop.linter.rules import ProjectChecker, Rule, RuleSeverity
from robocop.source_file import SourceFile, VirtualSourceFile


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

    def scan_project(self, project_source_file: VirtualSourceFile, config_manager: ConfigManager) -> None:
        files_count = 0
        for robot_file in config_manager.root.rglob("*.robot"):
            files_count += 1
            self.report(self.project_checker, source=SourceFile(robot_file, config=project_source_file.config))
        # files can be also parsed (with get_model) and checked here
        self.report(
            self.test_total_count,
            source=SourceFile(Path("Project-name"), project_source_file.config),
            files=files_count,
        )

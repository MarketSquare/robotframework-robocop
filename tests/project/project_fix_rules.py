from __future__ import annotations

from typing import TYPE_CHECKING

from robocop.linter.fix import Fix, FixApplicability, FixAvailability, TextEdit
from robocop.linter.rules import FixableRule, ProjectChecker, RuleSeverity

if TYPE_CHECKING:
    from robocop.config.manager import ConfigManager
    from robocop.linter.diagnostics import Diagnostic
    from robocop.project.context import ProjectContext
    from robocop.source_file import VirtualSourceFile


class RenamedKeywordRule(FixableRule):
    """Custom project rule with a fix. Reports calls of the ``Old Keyword`` keyword."""

    name = "renamed-keyword"
    rule_id = "PFX01"
    message = "Keyword '{keyword_name}' was renamed to 'New Keyword'"
    severity = RuleSeverity.WARNING
    added_in_version = "9.0.0"
    project_rule = True
    fix_availability = FixAvailability.ALWAYS

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:  # noqa: ARG002
        return Fix(
            edits=[TextEdit.replace_at_range(self.rule_id, self.name, diag.range, "New Keyword")],
            message="Replace 'Old Keyword' with 'New Keyword'",
            applicability=FixApplicability.SAFE,
        )


class RenamedKeywordChecker(ProjectChecker):
    """Project checker reporting calls of the renamed keyword."""

    renamed_keyword: RenamedKeywordRule

    def scan_project(
        self,
        project_source_file: VirtualSourceFile,  # noqa: ARG002
        config_manager: ConfigManager,  # noqa: ARG002
        context: ProjectContext,
    ) -> None:
        for project_file, usage in context.iter_usages():
            if usage.normalized_name != "oldkeyword":
                continue
            self.report(
                self.renamed_keyword,
                source=project_file.source_file,
                keyword_name=usage.name,
                lineno=usage.location.lineno,
                col=usage.location.col,
                end_lineno=usage.location.end_lineno,
                end_col=usage.location.end_col,
            )

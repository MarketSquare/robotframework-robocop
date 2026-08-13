"""Tests for backwards compatibility of the ``scan_project`` interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robocop.linter.rules import ProjectChecker
from robocop.linter.runner import accepts_project_context

if TYPE_CHECKING:
    from robocop.config import ConfigManager
    from robocop.linter.diagnostics import VirtualSourceFile
    from robocop.project import ProjectContext


class LegacyChecker(ProjectChecker):
    """Custom checker written before the project context was introduced."""

    def scan_project(self, project_source_file: VirtualSourceFile, config_manager: ConfigManager) -> None:  # noqa: ARG002
        return


class ContextAwareChecker(ProjectChecker):
    """Custom checker using the project context."""

    def scan_project(
        self,
        project_source_file: VirtualSourceFile,  # noqa: ARG002
        config_manager: ConfigManager,  # noqa: ARG002
        context: ProjectContext | None = None,  # noqa: ARG002
    ) -> None:
        return


class KwargsChecker(ProjectChecker):
    """Custom checker accepting any future argument."""

    def scan_project(self, *args, **kwargs) -> None:  # noqa: ARG002
        return


class TestAcceptsProjectContext:
    def test_legacy_checker_does_not_accept_context(self):
        assert not accepts_project_context(LegacyChecker)

    def test_context_aware_checker_accepts_context(self):
        assert accepts_project_context(ContextAwareChecker)

    def test_kwargs_checker_accepts_context(self):
        assert accepts_project_context(KwargsChecker)

    def test_base_checker_accepts_context(self):
        assert accepts_project_context(ProjectChecker)

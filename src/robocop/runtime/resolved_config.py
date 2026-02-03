from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from robocop.formatter.formatters import Formatter
    from robocop.linter.rules import (
        AfterRunChecker,
        BaseChecker,
        ProjectChecker,
        Rule,
    )


@dataclass
class ResolvedConfig:
    checkers: list[BaseChecker]
    after_run_checkers: list[AfterRunChecker]
    project_checkers: list[ProjectChecker]
    rules: dict[str, Rule]
    formatters: dict[str, Formatter]

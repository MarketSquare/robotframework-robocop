from __future__ import annotations

from pathlib import Path

from robocop.linter.rules import Diagnostic


def generate_issues(rule, rule2, root_path: Path | None = None) -> list[Diagnostic]:
    root = Path.cwd() if root_path is None else root_path
    source1_rel = "tests/atest/rules/comments/ignored-data/test.robot"
    source2_rel = "tests/atest/rules/misc/empty-return/test.robot"
    source1 = str(root / source1_rel)
    source2 = str(root / source2_rel)
    return [
        Diagnostic(
            rule=r,
            source=source,
            node=None,
            lineno=line,
            col=col,
            end_lineno=end_line,
            end_col=end_col,
        )
        for r, source, line, end_line, col, end_col in [
            (rule, source1, 50, None, 10, None),
            (rule2, source1, 50, 51, 10, None),
            (rule, source2, 50, None, 10, 12),
            (rule2, source2, 11, 15, 10, 15),
        ]
    ]

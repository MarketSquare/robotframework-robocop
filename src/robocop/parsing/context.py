"""
Module for managing and storing the visitor current context.

Visitor set the context before visiting the node and clear it after.
Visitor manages scope.
"""

from dataclasses import dataclass

from robot.parsing.model import Statement
from robot.parsing.model.blocks import Keyword
from robot.parsing.model.statements import Comment, EmptyLine


@dataclass
class Context:
    keyword: Keyword | None = None

    @property
    def last_data_statement_in_keyword(self) -> Statement | None:
        if self.keyword is None:
            return None
        for statement in self.keyword.body[::-1]:
            if isinstance(statement, (EmptyLine, Comment)):
                continue
            return statement
        return None

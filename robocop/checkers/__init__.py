import ast
import re
import os
from pathlib import Path
from robot.parsing.model.statements import Documentation, Comment
from astroid import modutils
from robocop.messages import Message


"""
Message ids:
01: base
02: documentation
03: naming
04: errors
05: lengths
06: tags
07: comments
09: misc

"""


class BaseChecker(ast.NodeVisitor):
    def __init__(self, linter, configurable=None):
        self.linter = linter
        self.source = None
        self.messages = {}
        self.configurable = set() if configurable is None else configurable
        self.register_messages(self.msgs)  # TODO: Add pylint ignore rule

    def visit_File(self, node):
        self.generic_visit(node)
        
    def is_disabled(self, node, rule):
        for statement in node.body:
            if not isinstance(statement, Comment):
                continue
            if statement.lineno == node.lineno:
                comment = statement.get_token('COMMENT')
                if comment is None:
                    continue
                match = re.search(r'(.*robocop: )(?P<disable>disable=[^\s]*)', comment.value)
                if not match:
                    return False
                if match.group('disable') == f"disable={rule}":
                    return True

    def register_messages(self, msgs):
        for key, value in msgs.items():
            msg = Message(key, value)
            if msg.name in self.messages:
                raise ValueError("Duplicate message name in checker")  # TODO: add better handling for duplicate messages
            self.messages[msg.name] = msg
        
    def report(self, msg, *args, node=None, lineno=None, col=None):
        if msg not in self.messages:
            raise ValueError(f"Missing definition for message with name {msg}")
        message = self.messages[msg].prepare_message(*args, source=self.source, node=node, lineno=lineno, col=col)
        self.linter.report(message)

    def configure(self, param, value):
        self.__dict__[param] = value
        
def init(linter):
    seen = set()
    for file in Path(__file__).parent.iterdir():
        if file.stem in seen or '__pycache__' in str(file):
            continue
        try:
            if file.is_dir() or (file.suffix in ('.py') and file.stem != '__init__'):
                linter.write_line(f"Importing rule file {file}")
                module = modutils.load_module_from_file(str(file))
                module.register(linter)
                seen.add(file.stem)
        except Exception as e:
            linter.write_line(e)

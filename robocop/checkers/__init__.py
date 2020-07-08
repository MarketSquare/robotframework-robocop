import ast
import re
import os
from pathlib import Path
from robot.parsing.model.statements import Documentation, Comment
from astroid import modutils


"""
Message ids:
01: base
02: documentation
03: naming

"""


class BaseChecker(ast.NodeVisitor):
    def __init__(self, linter):
        self.linter = linter
        self.source = None

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
        
    def report(self, msgs, msg, node, *args, lineno=None, col=None):
        for key, value in msgs.items():
            if value[0] == msg:
                break
        else:
            raise ValueError(f'Missing definiton for message with name {msg}')
        msg = value[1]
        if args:
            msg %= args
        self.linter.report(key, msg, node, self.source, lineno, col)
        
def init(linter):
    seen = set()
    for file in Path(__file__).parent.iterdir():
        if file.stem in seen or '__pycache__' in str(file):
            continue
        try:
            if file.is_dir() or (file.suffix in ('.py') and file.stem != '__init__'):
                print(f"Importing rule file {file}")
                module = modutils.load_module_from_file(str(file))
                module.register(linter)
                seen.add(file.stem)
        except Exception as e:
            print(e)
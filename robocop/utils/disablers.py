"""
Collection of classes for detecting checker disablers (like # robocop: disable) in robot files
"""
import re
from collections import defaultdict
from copy import deepcopy

from robot.utils import FileReader

import robocop.exceptions


class DisablersInFile:  # pylint: disable=too-few-public-methods
    """Container for file disablers"""

    def __init__(self):
        self.lastblock = -1
        self.lines = set()
        self.blocks = []

    def copy(self):
        """Used by defaultdict to create new instance for every new key in disablers container"""
        return deepcopy(self)


class DisablersFinder:
    """Parse all scanned file and find and disablers (in line or blocks)"""

    def __init__(self, filename, source):
        self.file_disabled = False
        self.any_disabler = False
        self.disabler_pattern = re.compile(r"robocop: ?(?P<disabler>disable|enable)=?(?P<rules>[\w\-,]*)")
        self.rules = defaultdict(DisablersInFile().copy)
        if source is not None:
            self._parse_source(source)
        else:
            self._parse_file(filename)

    def is_rule_disabled(self, rule_msg):
        """
        Check if given `rule_msg` is disabled. All takes precedence, then line disablers, then block disablers.
        We're checking for both message id and name.
        """
        if not self.any_disabler:
            return False
        return any(
            self.is_line_disabled(line, rule)
            for line in (rule_msg.line, *rule_msg.ext_disablers)
            for rule in ("all", rule_msg.rule_id, rule_msg.name)
        )

    def is_line_disabled(self, line, rule):
        """Helper method for is_rule_disabled that check if given line is in range of any disabled block"""
        if rule not in self.rules:
            return False
        if line in self.rules[rule].lines:
            return True
        return any(block[0] <= line <= block[1] for block in self.rules[rule].blocks)

    def _parse_lines(self, lines):
        lineno = -1
        for lineno, line in enumerate(lines, start=1):
            if "#" in line:
                self._parse_line(line, lineno)
        if lineno == -1:
            return
        self._end_block("all", lineno)
        self.file_disabled = self._is_file_disabled(lineno)
        self.any_disabler = len(self.rules) != 0

    def _parse_file(self, filename):
        try:
            with FileReader(filename) as file_reader:
                lines = list(file_reader.readlines())
                self._parse_lines(lines)
        except OSError:
            raise robocop.exceptions.FileError(filename) from None
        except UnicodeDecodeError:
            print(f"Failed to decode {filename}. Default supported encoding by Robot Framework is UTF-8. Skipping file")
            self.file_disabled = True

    def _parse_source(self, source):
        self._parse_lines(source.splitlines())

    def _parse_line(self, line, lineno):
        statement, comment = line.split("#", maxsplit=1)
        if "# noqa" in line:
            self._add_inline_disabler("all", lineno)
        disabler = self.disabler_pattern.search(comment)
        if not disabler:
            return
        if not disabler.group("rules"):
            rules = ["all"]
        else:
            rules = disabler.group("rules").split(",")
        block = not statement.lstrip()  # block disabler ignores preceding whitespaces
        if disabler.group("disabler") == "disable":
            for rule in rules:
                if block:
                    self._start_block(rule, lineno)
                else:
                    self._add_inline_disabler(rule, lineno)
        elif disabler.group("disabler") == "enable" and block:
            for rule in rules:
                self._end_block(rule, lineno)

    def _is_file_disabled(self, last_line):
        """
        The file is disabled if all rules are disabled in every line - we need to iterate every block to see
        if they are linked from first to last line without breaks.
        """
        if "all" not in self.rules:
            return False
        prev_end = 1
        for block in self.rules["all"].blocks:
            if prev_end != block[0]:
                return False
            prev_end = block[1]
        return prev_end == last_line

    def _add_inline_disabler(self, rule, lineno):
        self.rules[rule].lines.add(lineno)

    def _start_block(self, rule, lineno):
        if self.rules[rule].lastblock == -1:
            self.rules[rule].lastblock = lineno

    def _end_block(self, rule, lineno):
        if rule == "all":
            self._end_all_blocks(lineno)
        if rule not in self.rules:
            return
        if self.rules[rule].lastblock != -1:
            block = (self.rules[rule].lastblock, lineno)
            self.rules[rule].lastblock = -1
            self.rules[rule].blocks.append(block)

    def _end_all_blocks(self, lineno):
        for rule in self.rules:
            if rule == "all":
                continue  # to avoid recursion
            self._end_block(rule, lineno)

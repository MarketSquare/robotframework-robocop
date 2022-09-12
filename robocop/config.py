import argparse
import fnmatch
import os
import re
import sys
from itertools import chain
from pathlib import Path
from typing import Dict, Pattern, Set

import tomli
from robot.utils import FileReader

from robocop.exceptions import (
    ArgumentFileNotFoundError,
    ConfigGeneralError,
    InvalidArgumentError,
    NestedArgumentFileError,
)
from robocop.files import DEFAULT_EXCLUDES, find_file_in_project_root, find_project_root
from robocop.rules import RuleSeverity
from robocop.utils import RecommendationFinder
from robocop.version import __version__


def translate_pattern(pattern: str) -> Pattern:
    return re.compile(fnmatch.translate(pattern))


class ParseDelimitedArgAction(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        container = getattr(namespace, self.dest)
        config_values = values.split(",")
        if isinstance(container, list):
            container.extend(config_values)
        else:
            container.update(values.split(","))


class ParseCheckerConfig(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        container = getattr(namespace, self.dest)
        container.append(values.strip())


class ParseFileTypes(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        filetypes = getattr(namespace, self.dest)
        for filetype in values.split(","):
            filetypes.add(filetype if filetype.startswith(".") else "." + filetype)
        setattr(namespace, self.dest, filetypes)


class SetRuleThreshold(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, RuleSeverity.parser(values, rule_severity=False))


class SetListOption(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pattern = values if values else "*"
        if "*" in pattern:
            pattern = translate_pattern(pattern)
        setattr(namespace, self.dest, pattern)


class CustomArgParser(argparse.ArgumentParser):
    def __init__(self, *args, from_cli=False, **kwargs):
        self.from_cli = from_cli
        super().__init__(*args, **kwargs)

    def error(self, message):
        if self.from_cli:
            super().error(message)
        else:
            raise InvalidArgumentError(message)


def validate_regex(pattern: str) -> Pattern:
    try:
        return re.compile(pattern) if pattern is not None else None
    except re.error:
        raise ConfigGeneralError(f"Provided regex pattern {pattern} failed to be compiled")


class Config:
    def __init__(self, root=None, from_cli: bool = False):
        self.from_cli = from_cli
        self.exec_dir = os.path.abspath(".")
        self.root = Path(root) if root is not None else root
        self.include = set()
        self.exclude = set()
        self.ignore = set()
        self.ignore_default = re.compile(DEFAULT_EXCLUDES)
        self.reports = ["return_status"]
        self.threshold = RuleSeverity("I")
        self.configure = []
        self.format = "{source}:{line}:{col} [{severity}] {rule_id} {desc} ({name})"
        self.paths = ["."]
        self.ext_rules = set()
        self.include_patterns = []
        self.exclude_patterns = []
        self.filetypes = {".robot", ".resource", ".tsv"}
        self.language = []
        self.list = ""
        self.list_configurables = ""
        self.list_reports = False
        self.output = None
        self.recursive = True
        self.verbose = False
        self.config_from = ""
        self.parser = self._create_parser()
        self.parse_opts(from_cli=from_cli)

    def remove_severity(self):
        self.include = {self.replace_severity_values(rule) for rule in self.include}
        self.exclude = {self.replace_severity_values(rule) for rule in self.exclude}
        for index, conf in enumerate(self.configure):
            if conf.count(":") != 2:
                continue
            message, param, value = conf.split(":")
            message = self.replace_severity_values(message)
            self.configure[index] = f"{message}:{param}:{value}"

    @staticmethod
    def filter_patterns_from_names(only_names, only_patterns):
        filtered = set()
        for rule in only_names:
            if "*" in rule:
                only_patterns.append(translate_pattern(rule))
            else:
                filtered.add(rule)
        return filtered

    def translate_patterns(self):
        self.include = self.filter_patterns_from_names(self.include, self.include_patterns)
        self.exclude = self.filter_patterns_from_names(self.exclude, self.exclude_patterns)

    def _create_parser(self):
        parser = CustomArgParser(
            prog="robocop",
            formatter_class=argparse.RawTextHelpFormatter,
            description="Static code analysis tool for Robot Framework",
            epilog="For full documentation visit: https://robocop.readthedocs.io/en/latest/",
            add_help=False,
            from_cli=self.from_cli,
        )
        required = parser.add_argument_group(title="Required parameters")
        optional = parser.add_argument_group(title="Optional parameters")

        required.add_argument(
            "paths",
            metavar="paths",
            type=str,
            nargs="*",
            default=self.paths,
            help="List of paths (files or directories) to be parsed by Robocop.",
        )
        optional.add_argument(
            "-i",
            "--include",
            action=ParseDelimitedArgAction,
            default=self.include,
            metavar="RULES",
            help="Run Robocop only with specified rules. You can define rule by its name or id.\n"
            "Glob patterns are supported.",
        )
        optional.add_argument(
            "-e",
            "--exclude",
            action=ParseDelimitedArgAction,
            default=self.exclude,
            metavar="RULES",
            help="Ignore specified rules. You can define rule by its name or id.\nGlob patterns are supported.",
        )
        optional.add_argument(
            "-rules",
            "--ext-rules",
            action=ParseDelimitedArgAction,
            default=self.ext_rules,
            help="List of paths with custom rules.",
        )
        optional.add_argument(
            "-nr",
            "--no-recursive",
            dest="recursive",
            action="store_false",
            help="Use this flag to stop scanning directories recursively.",
        )
        optional.add_argument(
            "-r",
            "--reports",
            action=ParseDelimitedArgAction,
            default=self.reports,
            help="Generate reports after scan.\n"
            "You can enable reports by listing them in comma-separated list:\n"
            "--reports rules_by_id,rules_by_error_type,scan_timer\n"
            "To enable all reports use all:\n"
            "--reports all",
        )
        optional.add_argument(
            "-f",
            "--format",
            type=str,
            default=self.format,
            help="Format of output message. "
            "You can use placeholders to change the way an issue is reported.\n"
            "Default: {source}:{line}:{col} [{severity}] {rule_id} {desc} ({name})",
        )
        optional.add_argument(
            "-c",
            "--configure",
            action=ParseCheckerConfig,
            default=self.configure,
            metavar="CONFIGURABLE",
            help="Configure checker or report with parameter value. Usage:\n"
            "-c message_name_or_id:param_name:param_value\n"
            "Examples:\n"
            "-c line-too-long:line_length:150\n"
            "--configure 0101:severity:E",
        )
        optional.add_argument(
            "-l",
            "--list",
            action=SetListOption,
            nargs="?",
            const="",
            default=self.list,
            metavar="PATTERN",
            help="List all available rules. You can use optional PATTERN argument.",
        )
        optional.add_argument(
            "-lc",
            "--list-configurables",
            action=SetListOption,
            nargs="?",
            const="",
            default=self.list_configurables,
            metavar="PATTERN",
            help="List all available rules with configurable parameters. You can use optional PATTERN argument.",
        )
        optional.add_argument(
            "-lr",
            "--list-reports",
            action="store_true",
            default=self.list_reports,
            help="List all available reports.",
        )
        optional.add_argument(
            "-o",
            "--output",
            type=argparse.FileType("w"),
            default=self.output,
            metavar="PATH",
            help="Path to output file.",
        )
        optional.add_argument(
            "-ft",
            "--filetypes",
            action=ParseFileTypes,
            default=self.filetypes,
            help="Comma-separated list of file extensions to be scanned by Robocop",
        )
        optional.add_argument(
            "-t",
            "--threshold",
            action=SetRuleThreshold,
            default=self.threshold,
            help=f"Disable rules below given threshold. Available message levels: "
            f'{" < ".join(sev.value for sev in RuleSeverity)}',
        )
        optional.add_argument("-A", "--argumentfile", metavar="PATH", help="Path to file with arguments.")
        optional.add_argument(
            "-g",
            "--ignore",
            action=ParseDelimitedArgAction,
            default=self.ignore,
            metavar="PATH",
            help="Ignore file(s) and path(s) provided. Glob patterns are supported.",
        )
        optional.add_argument(
            "-gd",
            "--ignore-default",
            type=validate_regex,
            default=self.ignore_default,
            metavar="PATTERN",
            help=f"Paths ignored by default. "
            f"A regular expression to exclude directories on file search.\n"
            f"An empty value means no path is excluded. Default: {DEFAULT_EXCLUDES}",
        )
        optional.add_argument(
            "--language",
            "--lang",
            action=ParseDelimitedArgAction,
            default=self.language,
            help="Parse Robot Framework files using additional languages.",
        )
        optional.add_argument("-h", "--help", action="help", help="Print this help message and exit.")
        optional.add_argument(
            "-v",
            "--version",
            action="version",
            version=__version__,
            help="Display Robocop version.",
        )
        optional.add_argument(
            "-vv", "--verbose", action="store_true", help="Display extra information during execution."
        )
        optional.add_argument(
            "--directives",
            action="version",
            version="1. Serve the public trust\n2. Protect the innocent\n3. Uphold the law\n4. [ACCESS " "DENIED]",
            help=argparse.SUPPRESS,
        )

        return parser

    def parse_opts(self, args=None, from_cli: bool = True):
        if self.root is None:
            self.root = find_project_root(self.paths)
        self.load_default_config_file()

        if from_cli:
            args = self.parse_args(args)
        else:
            args = None

        self.remove_severity()
        self.translate_patterns()
        self.print_config_source()

        return args

    def print_config_source(self):
        # We can only print after reading all configs, since self.verbose is unknown before we read it from config
        # TODO self.config_from can be multiple configs (if it's from argumentfile)
        if not self.verbose:
            return
        if self.config_from:
            print(f"Loaded configuration from {self.config_from}")
        else:
            print("No config file found or configuration is empty. Using default configuration")

    def load_default_config_file(self):
        if not self.load_robocop_file():
            self.load_pyproject_file()

    def load_robocop_file(self):
        """Returns True if .robocop exists"""
        robocop_path = find_file_in_project_root(".robocop", self.root)
        if not robocop_path.is_file():
            return False
        args = self.load_args_from_file(robocop_path)
        self.parse_args(args)
        return True

    def load_pyproject_file(self):
        pyproject_path = find_file_in_project_root("pyproject.toml", self.root)
        if not pyproject_path.is_file():
            return
        config_dir = pyproject_path.parent
        try:
            with Path(pyproject_path).open("rb") as fp:
                config = tomli.load(fp)
        except tomli.TOMLDecodeError as err:
            raise InvalidArgumentError(f"Failed to decode {str(pyproject_path)}: {err}") from None
        config = config.get("tool", {}).get("robocop", {})
        if self.parse_toml_to_config(config, config_dir):
            self.config_from = pyproject_path

    def parse_args_to_config(self, args):
        if args is None:
            return None

        args = self.parser.parse_args(args)
        for key, value in dict(**vars(args)).items():
            if key in self.__dict__:
                self.__dict__[key] = value

        return args

    def parse_args(self, args):
        args = self.preparse(args)
        if args:
            args = self.parse_args_to_config(args)
        return args

    def preparse(self, args):
        args = sys.argv[1:] if args is None else args
        parsed_args = []
        args = (arg for arg in args)
        for arg in args:
            if arg in ("-A", "--argumentfile"):
                try:
                    argfile = next(args)
                except StopIteration:
                    raise ArgumentFileNotFoundError("") from None
                parsed_args += self.load_args_from_file(argfile)
            else:
                parsed_args.append(arg)
        return parsed_args

    def load_args_from_file(self, argfile):
        try:
            with FileReader(argfile) as arg_f:
                args = []
                for line in arg_f.readlines():
                    if line.strip().startswith("#"):
                        continue
                    for arg in line.split(" ", 1):
                        arg = arg.strip()
                        if not arg:
                            continue
                        args.append(arg)
                if "-A" in args or "--argumentfile" in args:
                    raise NestedArgumentFileError(argfile)
                if args:
                    self.config_from = argfile
                return args
        except FileNotFoundError:
            raise ArgumentFileNotFoundError(argfile) from None

    @staticmethod
    def replace_in_set(container: Set, old_key: str, new_key: str):
        if old_key not in container:
            return
        container.remove(old_key)
        container.add(new_key)

    def validate_rule_names(self, rules):
        # add rule name in form of old_name: new_name
        deprecated = {}
        for rule in chain(self.include, self.exclude):
            if rule in deprecated:  # update warning description to specific case
                print(
                    f"### DEPRECATION WARNING ###\nThe name (or ID) of the rule '{rule}' is "
                    f"renamed to '{deprecated[rule]}'. "
                    f"Update your configuration if you're using old name. "
                    f"This information will disappear in the next version (X.Y.Z)\n\n"
                )
                self.replace_in_set(self.include, rule, deprecated[rule])
                self.replace_in_set(self.exclude, rule, deprecated[rule])
            elif rule not in rules:
                similar = RecommendationFinder().find_similar(rule, rules)
                raise ConfigGeneralError(f"Provided rule '{rule}' does not exist. {similar}")

    def is_rule_enabled(self, rule):
        if self.is_rule_disabled(rule):
            return False
        if self.include or self.include_patterns:  # if any include pattern, it must match with something
            if rule.rule_id in self.include or rule.name in self.include:
                return True
            for pattern in self.include_patterns:
                if pattern.match(rule.rule_id) or pattern.match(rule.name):
                    return True
            return False
        return True

    def is_rule_disabled(self, rule):
        if not rule.enabled_in_version:
            return True
        if rule.severity < self.threshold:
            return True
        if rule.rule_id in self.exclude or rule.name in self.exclude:
            return True
        for pattern in self.exclude_patterns:
            if pattern.match(rule.rule_id) or pattern.match(rule.name):
                return True
        return False

    def is_path_ignored(self, path):
        for pattern in self.ignore:
            if path.match(pattern):
                return True
        if self.ignore_default:
            match = self.ignore_default.search(str(path))
            return bool(match and match.group(0))
        return False

    @staticmethod
    def replace_severity_values(rule_name: str):
        sev = "".join(sev.value for sev in RuleSeverity)
        if re.match(f"[{sev}][0-9]{{4,}}", rule_name):
            for char in sev:
                rule_name = rule_name.replace(char, "")
        return rule_name

    def resolve_relative(self, orig_path, config_dir: Path, ensure_exists: bool):
        path = Path(orig_path)
        if path.is_absolute():
            return orig_path
        resolved_path = config_dir / path
        if not ensure_exists or resolved_path.exists():
            return str(resolved_path)
        return orig_path

    def parse_toml_to_config(self, toml_data: Dict, config_dir: Path):
        if not toml_data:
            return False
        resolve_relative = {"paths", "ext_rules", "output"}
        assign_type = {"paths", "format"}
        set_type = {"include", "exclude", "ignore", "ext_rules"}
        append_type = {"configure", "reports", "language"}
        toml_data = {key.replace("-", "_"): value for key, value in toml_data.items()}
        for key, value in toml_data.items():
            if key in resolve_relative:
                if isinstance(value, list):
                    for index, val in enumerate(value):
                        value[index] = self.resolve_relative(val, config_dir, ensure_exists=key == "ext_rules")
                else:
                    value = self.resolve_relative(value, config_dir, ensure_exists=key == "ext_rules")
            if key in assign_type:
                self.__dict__[key] = value
            elif key in set_type:
                self.__dict__[key].update(set(value))
            elif key in append_type:
                self.__dict__[key] += value
            elif key == "filetypes":
                for filetype in toml_data["filetypes"]:
                    self.filetypes.add(filetype if filetype.startswith(".") else "." + filetype)
            elif key == "threshold":
                self.threshold = RuleSeverity(value)
            elif key == "output":
                self.output = open(value, "w")
            elif key == "no_recursive":
                self.recursive = not value
            elif key == "verbose":
                self.verbose = value
            else:
                raise InvalidArgumentError(f"Option '{key}' is not supported in pyproject.toml configuration file.")
        return True

import argparse
import fnmatch
import os
import re
import sys
from itertools import chain
from pathlib import Path
from re import Pattern
from typing import TYPE_CHECKING

import tomli
from robot.utils import FileReader

from robocop import exceptions
from robocop.files import DEFAULT_EXCLUDES, find_file_in_project_root, find_project_root
from robocop.rules import RuleFilter, RuleSeverity
from robocop.version import __version__

if TYPE_CHECKING:
    from robocop.rules import Rule


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
        pattern = values if values else RuleFilter.DEFAULT
        if "*" in pattern:
            pattern = translate_pattern(pattern)
        setattr(namespace, self.dest, pattern)


class SetOptionalValue(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        value = value if value else "default"
        setattr(namespace, self.dest, value)


class CustomArgParser(argparse.ArgumentParser):
    def __init__(self, *args, from_cli=False, **kwargs):
        self.from_cli = from_cli
        super().__init__(*args, **kwargs)

    def error(self, message):
        if self.from_cli:
            super().error(message)
        else:
            raise exceptions.InvalidArgumentError(message)


def validate_regex(pattern: str) -> Pattern:
    try:
        return re.compile(pattern) if pattern is not None else None
    except re.error:
        raise exceptions.ConfigGeneralError(f"Provided regex pattern {pattern} failed to be compiled")


def resolve_relative_path(orig_path, config_dir: Path, ensure_exists: bool):
    path = Path(orig_path)
    if path.is_absolute():
        return orig_path
    resolved_path = config_dir / path
    if not ensure_exists or resolved_path.exists():
        return str(resolved_path)
    return orig_path


class ArgumentFileParser:
    ARGUMENT_FILE_OPTIONS = {"-A", "--argumentfile"}
    RESOLVE_PATHS_OPTIONS = {"-o", "--output", "-rules", "--ext-rules"}
    ENSURE_EXIST_PATHS_OPTIONS = {"-rules", "--ext-rules"}

    def __init__(self):
        self.loaded_argument_files = set()
        self.config_from = ""

    def expand_argument_files(self, args, config_dir=None):
        """Find argument files in the argument list and expand argument list with their content."""
        if not any(arg in self.ARGUMENT_FILE_OPTIONS for arg in args):
            return list(args)
        parsed_args = []
        while args:
            arg = args.pop(0)
            if arg not in self.ARGUMENT_FILE_OPTIONS:
                parsed_args.append(arg)
                continue
            if not args:  # argumentfile option declared but filename was not provided
                raise exceptions.ArgumentFileNotFoundError("") from None  # TODO: denote that file was not provided
            argfile = args.pop(0)
            argfile_path = Path(argfile)
            if argfile_path.is_file():
                loaded_config_dir = argfile_path.parent
            else:
                loaded_config_dir = None
            file_args = self.load_argument_file(argfile, config_dir)
            file_args = self.resolve_arguments_paths(file_args, loaded_config_dir)
            parsed_args += self.expand_argument_files(file_args, loaded_config_dir)
        return parsed_args

    def resolve_arguments_paths(self, args, root_dir):
        if root_dir is None:
            return args
        prev_option_like = False
        prev_arg = "option"
        resolved = []
        for arg in args:
            option_like = arg.startswith("-")
            # resolve path if previous arg was an option that can be path, or the arg is a source
            if (prev_option_like and prev_arg in self.RESOLVE_PATHS_OPTIONS) or (  # option value that can be path
                not prev_option_like and not option_like  # source
            ):
                ensure_exists = prev_arg in self.ENSURE_EXIST_PATHS_OPTIONS
                # TODO: If the --rules is provided as comma separated list, it will not resolve paths
                arg = resolve_relative_path(arg, root_dir, ensure_exists)  # noqa: PLW2901
            resolved.append(arg)
            prev_option_like = option_like
            prev_arg = arg
        return resolved

    def load_argument_file(self, argfile, config_dir):
        if config_dir is not None:
            argfile = resolve_relative_path(argfile, config_dir, True)
        if argfile in self.loaded_argument_files:
            raise exceptions.CircularArgumentFileError(argfile) from None
        self.loaded_argument_files.add(argfile)
        try:
            with FileReader(argfile) as arg_f:
                args = []
                for line in arg_f.readlines():
                    if line.strip().startswith("#"):
                        continue
                    args.extend([arg.strip() for arg in line.split(" ", 1) if arg.strip()])
                if args and not self.config_from:
                    self.config_from = argfile
                return args
        except FileNotFoundError:
            raise exceptions.ArgumentFileNotFoundError(argfile) from None


class Config:
    def __init__(self, root=None, from_cli: bool = False):
        self.from_cli = from_cli
        self.exec_dir = os.path.abspath(".")
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
        self.list_reports = ""
        self.output = None
        self.recursive = True
        self.verbose = False
        self.persistent = False
        self.ignore_git_dir = False
        self.config_from = ""
        self.root = find_project_root(root, ["."])
        self.parse()

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
            default=self.recursive,
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
            "To enable all default reports use 'all':\n"
            "--reports all\n"
            "List available reports with --list-reports option.",
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
            help="List all available rules. You can use optional PATTERN argument to match rule names "
            "(for example --list *doc*). "
            "PATTERN can be also ENABLED/DISABLED keyword to list only enabled/disabled rules.",
        )
        optional.add_argument(
            "-lc",
            "--list-configurables",
            action=SetListOption,
            nargs="?",
            const="",
            default=self.list_configurables,
            metavar="PATTERN",
            help="List all available rules with configurable parameters. You can use optional PATTERN argument "
            "to match rule names (for example --list *doc*). "
            "PATTERN can be also ENABLED/DISABLED keyword to list only enabled/disabled rules.",
        )
        optional.add_argument(
            "-lr",
            "--list-reports",
            action=SetOptionalValue,
            nargs="?",
            const="",
            default=self.list_reports,
            metavar="ENABLED/DISABLED",
            help="List all available reports. "
            "Pass ENABLED or DISABLED as argument to list only enabled/disabled reports.",
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
        optional.add_argument("--config", metavar="PATH", help="Path to TOML configuration file.")
        optional.add_argument(
            "--ignore-git-dir",
            action="store_true",
            default=self.ignore_git_dir,
            help="Use this flag to continue searching for the default configuration file even if parent directory "
            "contains '.git' directory. Useful for multirepo.",
        )
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
        optional.add_argument(
            "--persistent",
            action="store_true",
            default=self.persistent,
            help="Use this flag to save Robocop reports in cache directory for later comparison.",
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
            "-vv",
            "--verbose",
            action="store_true",
            default=self.verbose,
            help="Display extra information during execution.",
        )
        optional.add_argument(
            "--directives",
            action="version",
            version="1. Serve the public trust\n2. Protect the innocent\n3. Uphold the law\n4. [ACCESS DENIED]",
            help=argparse.SUPPRESS,
        )

        return parser

    def parse(self):
        if not self.from_cli:
            self.load_default_config_file()
            return
        args = sys.argv[1:]
        if not self.config_file_in_cli(args):
            self.load_default_config_file(ignore_git_dir="--ignore-git-dir" in args)
        self.parse_args(args)

    @staticmethod
    def config_file_in_cli(args):
        config_options = {"-A", "--argumentfile", "--config"}
        return any(arg in config_options for arg in args)

    def reload(self, rules):
        self.remove_severity()
        self.translate_patterns()
        self.print_config_source()
        self.validate_rules_exists_and_not_deprecated(rules)

    def print_config_source(self):
        # We can only print after reading all configs, since self.verbose is unknown before we read it from config
        if not self.verbose:
            return
        if self.config_from:
            print(f"Loaded configuration from {self.config_from}")
        else:
            print("No config file found or configuration is empty. Using default configuration")

    def load_default_config_file(self, ignore_git_dir: bool = False):
        """
        Find and load default configuration file.

        First look for .robocop file. If it does not exist, search for pyproject.toml file.
        """
        if self.load_robocop_file(ignore_git_dir):
            return
        pyproject_path = find_file_in_project_root("pyproject.toml", self.root, ignore_git_dir)
        if pyproject_path is not None:
            self.load_pyproject_file(pyproject_path)

    def load_robocop_file(self, ignore_git_dir: bool):
        """Return True if .robocop exists"""
        robocop_path = find_file_in_project_root(".robocop", self.root, ignore_git_dir)
        if robocop_path is None:
            return False
        argument_files_parser = ArgumentFileParser()
        args = argument_files_parser.load_argument_file(robocop_path, robocop_path.parent)
        self.config_from = argument_files_parser.config_from
        self.parse_args(args)
        return True

    def load_pyproject_file(self, pyproject_path):
        config_dir = pyproject_path.parent
        try:
            with Path(pyproject_path).open("rb") as fp:
                config = tomli.load(fp)
        except tomli.TOMLDecodeError as err:
            raise exceptions.InvalidArgumentError(f"Failed to decode {pyproject_path!s}: {err}") from None
        config = config.get("tool", {}).get("robocop", {})
        if self.parse_toml_to_config(config, config_dir):
            self.config_from = pyproject_path

    def parse_args_to_config(self, args):
        parser = self._create_parser()
        args = parser.parse_args(args)
        if args.config is not None:
            config_path = Path(args.config)
            if not config_path.is_file():
                raise exceptions.TomlFileNotFoundError(str(config_path)) from None
            self.load_pyproject_file(config_path)
        for key, value in dict(**vars(args)).items():
            if key in self.__dict__:
                self.__dict__[key] = value

    def parse_args(self, args):
        argument_files_parser = ArgumentFileParser()
        args = argument_files_parser.expand_argument_files(args)
        if argument_files_parser.config_from:
            self.config_from = argument_files_parser.config_from
        self.parse_args_to_config(args)

    @staticmethod
    def replace_in_set(container: set, old_key: str, new_key: str):
        if old_key not in container:
            return
        container.remove(old_key)
        container.add(new_key)

    def validate_rules_exists_and_not_deprecated(self, rules: dict[str, "Rule"]):
        for rule in chain(self.include, self.exclude):
            if rule not in rules:
                raise exceptions.RuleDoesNotExist(rule, rules) from None
            rule_def = rules[rule]
            if rule_def.deprecated:
                print(rule_def.deprecation_warning)

    def is_rule_enabled(self, rule: "Rule") -> bool:
        if self.is_rule_disabled(rule):
            return False
        if self.include or self.include_patterns:  # if any include pattern, it must match with something
            if rule.rule_id in self.include or rule.name in self.include:
                return True
            return any(pattern.match(rule.rule_id) or pattern.match(rule.name) for pattern in self.include_patterns)
        return rule.enabled

    def is_rule_disabled(self, rule: "Rule") -> bool:
        if rule.deprecated or not rule.enabled_in_version:
            return True
        if rule.severity < self.threshold and not rule.config.get("severity_threshold"):
            return True
        if rule.rule_id in self.exclude or rule.name in self.exclude:
            return True
        return any(pattern.match(rule.rule_id) or pattern.match(rule.name) for pattern in self.exclude_patterns)

    def is_path_ignored(self, path) -> bool:
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

    def parse_toml_to_config(self, toml_data: dict, config_dir: Path):
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
                        value[index] = resolve_relative_path(val, config_dir, ensure_exists=key == "ext_rules")
                else:
                    value = resolve_relative_path(value, config_dir, ensure_exists=key == "ext_rules")  # noqa: PLW2901
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
                self.output = open(value, "w")  # noqa: SIM115
            elif key == "no_recursive":
                self.recursive = not value
            elif key == "verbose":
                self.verbose = value
            elif key == "persistent":
                self.persistent = value
            else:
                raise exceptions.InvalidArgumentError(
                    f"Option '{key}' is not supported in pyproject.toml configuration file."
                ) from None
        return True

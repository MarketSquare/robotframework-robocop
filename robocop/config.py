import argparse
import fnmatch
from pathlib import Path
from itertools import chain
import os
import re
import sys

try:
    import toml
    TOML_SUPPORT = True
except ImportError:
    TOML_SUPPORT = False

from robocop.exceptions import (
    ArgumentFileNotFoundError,
    NestedArgumentFileError,
    InvalidArgumentError,
    ConfigGeneralError
)
from robocop.rules import RuleSeverity
from robocop.version import __version__
from robocop.utils import RecommendationFinder


def translate_pattern(pattern):
    return re.compile(fnmatch.translate(pattern))


def parse_toml_to_config(toml_data, config):
    if not toml_data:
        return
    assign_type = {'paths', 'format', 'configure'}
    set_type = {'include', 'exclude', 'reports', 'ignore', 'ext_rules'}
    toml_data = {key.replace('-', '_'): value for key, value in toml_data.items()}
    for key, value in toml_data.items():
        if key in assign_type:
            config.__dict__[key] = value
        elif key in set_type:
            config.__dict__[key].update(set(value))
        elif key == 'filetypes':
            for filetype in toml_data['filetypes']:
                config.filetypes.add(filetype if filetype.startswith('.') else '.' + filetype)
        elif key == 'threshold':
            config.threshold = find_severity_value(value)
        elif key == 'output':
            config.output = open(value, 'w')
        elif key == 'no_recursive':
            config.recursive = not value
        elif key == 'verbose':
            config.verbose = value
        else:
            raise InvalidArgumentError(f"Option '{key}' is not supported in pyproject.toml configuration file.")


def find_severity_value(severity):
    for sev in RuleSeverity:
        if sev.value == severity.upper():
            return sev
    return RuleSeverity.INFO


class ParseDelimitedArgAction(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        container = getattr(namespace, self.dest)
        container.update(values.split(','))


class ParseCheckerConfig(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        container = getattr(namespace, self.dest)
        for value in values.split(','):
            container.append(value.strip())


class ParseFileTypes(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        filetypes = getattr(namespace, self.dest)
        for filetype in values.split(','):
            filetypes.add(filetype if filetype.startswith('.') else '.' + filetype)
        setattr(namespace, self.dest, filetypes)


class SetRuleThreshold(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, find_severity_value(values))


class SetListOption(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pattern = values if values else '*'
        if '*' in pattern:
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


class Config:
    def __init__(self, root=None, from_cli=False):
        self.from_cli = from_cli
        self.exec_dir = os.path.abspath('.')
        self.root = Path(root) if root is not None else root
        self.include = set()
        self.exclude = set()
        self.ignore = set()
        self.reports = {'return_status'}
        self.threshold = RuleSeverity.INFO
        self.configure = []
        self.format = "{source}:{line}:{col} [{severity}] {rule_id} {desc} ({name})"
        self.paths = ['.']
        self.ext_rules = set()
        self.include_patterns = []
        self.exclude_patterns = []
        self.filetypes = {'.robot', '.resource', '.tsv'}
        self.list = ''
        self.list_configurables = ''
        self.list_reports = False
        self.output = None
        self.recursive = True
        self.verbose = False
        self.config_from = ''
        self.parser = self._create_parser()

    HELP_MSGS = {
        'help_paths':        'List of paths (files or directories) to be parsed by Robocop.',
        'help_include':      'Run Robocop only with specified rules. You can define rule by its name or id.\n'
                             'Glob patterns are supported.',
        'help_exclude':      'Ignore specified rules. You can define rule by its name or id.\n'
                             'Glob patterns are supported.',
        'help_ext_rules':    'List of paths with custom rules.',
        'help_reports':      'Generate reports after scan. You can enable reports by listing them in comma\n'
                             'separated list:\n'
                             '--reports rules_by_id,rules_by_error_type,scan_timer\n'
                             'To enable all reports use all:\n'
                             '--report all',
        'help_format':       'Format of output message. '
                             'You can use placeholders to change the way an issue is reported.\n'
                             'Default: {source}:{line}:{col} [{severity}] {rule_id} {desc} ({name})',
        'help_configure':    'Configure checker with parameter value. Usage:\n'
                             '-c message_name_or_id:param_name:param_value\nExample:\n'
                             '-c line-too-long:line_length:150\n'
                             '--configure 0101:severity:E',
        'help_list':         'List all available rules. You can use optional pattern argument.',
        'help_list_confs':   'List all available rules with configurable parameters. '
                             'You can use optional pattern argument.',
        'help_list_reports': 'List all available reports.',
        'help_output':       'Path to output file.',
        'help_filetypes':    'Comma separated list of file extensions to be scanned by Robocop',
        'help_threshold':     f'Disable rules below given threshold. Available message levels: '
                              f'{" < ".join(sev.value for sev in RuleSeverity)}',
        'help_recursive':    'Use this flag to stop scanning directories recursively.',
        'help_argfile':      'Path to file with arguments.',
        'help_ignore':       'Ignore file(s) and path(s) provided. Glob patterns are supported.',
        'help_info':         'Print this help message and exit.',
        'help_version':      'Display Robocop version.',
        'help_verbose':      'Display extra information.',
        'directives':        '1. Serve the public trust\n2. Protect the innocent\n3. Uphold the law\n4. [ACCESS '
                             'DENIED]',
        'epilog':            'For full documentation visit: https://github.com/MarketSquare/robotframework-robocop'
    }

    def remove_severity(self):
        self.include = {self.replace_severity_values(rule) for rule in self.include}
        self.exclude = {self.replace_severity_values(rule) for rule in self.exclude}
        for index, conf in enumerate(self.configure):
            if conf.count(':') != 2:
                continue
            message, param, value = conf.split(':')
            message = self.replace_severity_values(message)
            self.configure[index] = f"{message}:{param}:{value}"

    @staticmethod
    def filter_patterns_from_names(only_names, only_patterns):
        filtered = set()
        for rule in only_names:
            if '*' in rule:
                only_patterns.append(translate_pattern(rule))
            else:
                filtered.add(rule)
        return filtered

    def translate_patterns(self):
        self.include = self.filter_patterns_from_names(self.include, self.include_patterns)
        self.exclude = self.filter_patterns_from_names(self.exclude, self.exclude_patterns)

    def preparse(self, args):
        args = sys.argv[1:] if args is None else args
        parsed_args = []
        args = (arg for arg in args)
        for arg in args:
            if arg in ('-A', '--argumentfile'):
                try:
                    argfile = next(args)
                except StopIteration:
                    raise ArgumentFileNotFoundError('') from None
                parsed_args += self.load_args_from_file(argfile)
            else:
                parsed_args.append(arg)
        return parsed_args

    def load_args_from_file(self, argfile):
        try:
            with open(argfile) as arg_f:
                args = [arg.strip() for line in arg_f for arg in line.split(' ', 1)]
                if '-A' in args or '--argumentfile' in args:
                    raise NestedArgumentFileError(argfile)
                self.config_from = argfile
                return args
        except FileNotFoundError:
            raise ArgumentFileNotFoundError(argfile) from None

    def _create_parser(self):
        parser = CustomArgParser(prog='robocop',
                                 formatter_class=argparse.RawTextHelpFormatter,
                                 description='Static code analysis tool for Robot Framework',
                                 epilog=self.HELP_MSGS['epilog'],
                                 add_help=False,
                                 from_cli=self.from_cli)
        required = parser.add_argument_group(title='Required parameters')
        optional = parser.add_argument_group(title='Optional parameters')

        required.add_argument('paths', metavar='paths', type=str, nargs='*', default=self.paths,
                              help=self.HELP_MSGS['help_paths'])
        optional.add_argument('-i', '--include', action=ParseDelimitedArgAction, default=self.include,
                              metavar='RULES', help=self.HELP_MSGS['help_include'])
        optional.add_argument('-e', '--exclude', action=ParseDelimitedArgAction, default=self.exclude,
                              metavar='RULES', help=self.HELP_MSGS['help_exclude'])
        optional.add_argument('-rules', '--ext-rules', action=ParseDelimitedArgAction, default=self.ext_rules,
                              help=self.HELP_MSGS['help_ext_rules'])
        optional.add_argument('-nr', '--no-recursive', dest='recursive', action='store_false',
                              help=self.HELP_MSGS['help_recursive'])
        optional.add_argument('-r', '--reports', action=ParseDelimitedArgAction, default=self.reports,
                              help=self.HELP_MSGS['help_reports'])
        optional.add_argument('-f', '--format', type=str, default=self.format, help=self.HELP_MSGS['help_format'])
        optional.add_argument('-c', '--configure', action=ParseCheckerConfig, default=self.configure,
                              metavar='CONFIGURABLE', help=self.HELP_MSGS['help_configure'])
        optional.add_argument('-l', '--list', action=SetListOption, nargs='?', const='', default=self.list,
                              metavar='PATTERN', help=self.HELP_MSGS['help_list'])
        optional.add_argument('-lc', '--list-configurables', action=SetListOption, nargs='?', const='',
                              default=self.list_configurables, metavar='PATTERN',
                              help=self.HELP_MSGS['help_list_confs'])
        optional.add_argument('-lr', '--list-reports', action='store_true', default=self.list_reports,
                              help=self.HELP_MSGS['help_list_reports'])
        optional.add_argument('-o', '--output', type=argparse.FileType('w'), default=self.output,
                              metavar='PATH', help=self.HELP_MSGS['help_output'])
        optional.add_argument('-ft', '--filetypes', action=ParseFileTypes, default=self.filetypes,
                              help=self.HELP_MSGS['help_filetypes'])
        optional.add_argument('-t', '--threshold', action=SetRuleThreshold, default=self.threshold,
                              help=self.HELP_MSGS['help_threshold'])
        optional.add_argument('-A', '--argumentfile', metavar='PATH', help=self.HELP_MSGS['help_argfile'])
        optional.add_argument('-g', '--ignore', action=ParseDelimitedArgAction, default=self.ignore,
                              metavar='PATH', help=self.HELP_MSGS['help_ignore'])
        optional.add_argument('-h', '--help', action='help', help=self.HELP_MSGS['help_info'])
        optional.add_argument('-v', '--version', action='version', version=__version__,
                              help=self.HELP_MSGS['help_version'])
        optional.add_argument('-vv', '--verbose', action='store_true', help=self.HELP_MSGS['help_verbose'])
        optional.add_argument('--directives', action='version', version=self.HELP_MSGS['directives'],
                              help=argparse.SUPPRESS)

        return parser

    def parse_opts(self, args=None, from_cli=True):
        args = self.preparse(args) if from_cli else None
        if not args or args == ['--verbose'] or args == ['-vv']:
            loaded_args = self.load_default_config_file()
            if loaded_args is None:
                self.load_pyproject_file()
            else:
                # thanks for this we can have config file together with some cli options like --verbose
                args = [*args, *loaded_args] if args is not None else loaded_args
        if args:
            args = self.parser.parse_args(args)
            for key, value in dict(**vars(args)).items():
                if key in self.__dict__:
                    self.__dict__[key] = value
        self.remove_severity()
        self.translate_patterns()
        if self.verbose:
            if self.config_from:
                print(f"Loaded configuration from {self.config_from}")
            else:
                print("No config file found. Using default configuration")

        return args

    def load_default_config_file(self):
        robocop_path = self.find_file_in_project_root('.robocop')
        if robocop_path.is_file():
            return self.load_args_from_file(robocop_path)
        return None

    def find_file_in_project_root(self, config_name):
        root = self.root or Path.cwd()
        for parent in (root, *root.parents):
            if (parent / '.git').exists() or (parent / config_name).is_file():
                return parent / config_name
        return parent / config_name

    def load_pyproject_file(self):
        if not TOML_SUPPORT:
            return
        pyproject_path = self.find_file_in_project_root('pyproject.toml')
        if not pyproject_path.is_file():
            return
        try:
            config = toml.load(str(pyproject_path))
        except toml.TomlDecodeError as err:
            raise InvalidArgumentError(f'Failed to decode {str(pyproject_path)}: {err}') from None
        config = config.get("tool", {}).get("robocop", {})
        parse_toml_to_config(config, self)
        self.config_from = pyproject_path

    @staticmethod
    def replace_in_set(container, old_key, new_key):
        if old_key not in container:
            return
        container.remove(old_key)
        container.add(new_key)

    def validate_rule_names(self, rules):
        deprecated = {
            'setting-name-not-capitalized': 'setting-name-not-in-title-case',
            'not-capitalized-keyword-name': 'wrong-case-in-keyword-name',
            'missing-doc-testcase': 'missing-doc-test-case'
        }
        for rule in chain(self.include, self.exclude):
            # TODO: Remove in 1.9.0
            if rule in deprecated:
                print(f"### DEPRECATION WARNING: The name of the rule '{rule}' is "
                      f"renamed to '{deprecated[rule]}' starting from Robocop 1.8.0. "
                      f"Update your configuration if you're using old name. ###\n")
                self.replace_in_set(self.include, rule, deprecated[rule])
                self.replace_in_set(self.exclude, rule, deprecated[rule])
            elif rule not in rules:
                similiar = RecommendationFinder().find_similar(rule, rules)
                raise ConfigGeneralError(f"Provided rule '{rule}' does not exist.{similiar}")

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
        return False

    @staticmethod
    def replace_severity_values(message):
        sev = ''.join(c.value for c in RuleSeverity)
        if re.match(f"[{sev}][0-9]{{4,}}", message):
            for char in sev:
                message = message.replace(char, '')
        return message

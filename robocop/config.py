import argparse
import fnmatch
import os
import re
import sys

from robocop.exceptions import ArgumentFileNotFoundError, NestedArgumentFileError
from robocop.rules import RuleSeverity
from robocop.version import __version__


def translate_pattern(pattern):
    return re.compile(fnmatch.translate(pattern))


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
        for sev in RuleSeverity:
            if sev.value == values:
                break
        else:
            sev = RuleSeverity.INFO
        setattr(namespace, self.dest, sev)


class SetListOption(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pattern = values if values else '*'
        if '*' in pattern:
            pattern = translate_pattern(pattern)
        setattr(namespace, self.dest, pattern)


class Config:
    def __init__(self):
        self.exec_dir = os.path.abspath('.')
        self.include = set()
        self.exclude = set()
        self.ignore = set()
        self.reports = {'return_status'}
        self.threshold = RuleSeverity.INFO
        self.configure = []
        self.format = "{source}:{line}:{col} [{severity}] {rule_id} {desc}"
        self.paths = []
        self.ext_rules = set()
        self.include_patterns = []
        self.exclude_patterns = []
        self.filetypes = {'.robot', '.resource', '.tsv'}
        self.list = ''
        self.list_configurables = ''
        self.output = None
        self.recursive = True
        self.parser = self._create_parser()

    HELP_MSGS = {
        'help_paths':       'List of paths (files or directories) to be parsed by Robocop',
        'help_include':     'Run Robocop only with specified rules. You can define rule by its name or id.\n'
                            'Glob patterns are supported',
        'help_exclude':     'Ignore specified rules. You can define rule by its name or id.\n'
                            'Glob patterns are supported',
        'help_ext_rules':   'List of paths with custom rules',
        'help_reports':     'Generate reports after scan. You can enable reports by listing them in comma\n'
                            'separated list:\n'
                            '--reports rules_by_id,rules_by_error_type\n'
                            'To enable all reports use all:\n'
                            '--report all',
        'help_format':      'Format of output message. '
                            'You can use placeholders to change the way an issue is reported.\n'
                            'Default: {source}:{line}:{col} [{severity}] {rule_id} {desc}',
        'help_configure':   'Configure checker with parameter value. Usage:\n'
                            '-c message_name_or_id:param_name:param_value\nExample:\n'
                            '-c line-too-long:line_length:150\n'
                            '--configure 0101:severity:E',
        'help_list':        'List all available rules. You can use optional pattern argument',
        'help_list_confs':  'List all available rules with configurable parameters. '
                            'You can use optional pattern argument',
        'help_output':      'Path to output file',
        'help_filetypes':   'Comma separated list of file extensions to be scanned by Robocop',
        'help_threshold':    f'Disable rules below given threshold. Available message levels: '
                             f'{" < ".join(sev.value for sev in RuleSeverity)}',
        'help_recursive':   'Use this flag to stop scanning directories recursively',
        'help_argfile':     'Path to file with arguments',
        'help_ignore':      'Ignore file(s) and path(s) provided. Glob patterns are supported',
        'help_info':        'Print this help message and exit',
        'help_version':     'Display Robocop version',
        'directives':       '1. Serve the public trust\n2. Protect the innocent\n3. Uphold the law\n4. [ACCESS DENIED]'
    }

    def _translate_patterns(self, pattern_list):
        return [translate_pattern(p) for p in pattern_list if '*' in p]

    def remove_severity(self):
        self.include = {self.replace_severity_values(rule) for rule in self.include}
        self.exclude = {self.replace_severity_values(rule) for rule in self.exclude}
        for index, conf in enumerate(self.configure):
            if conf.count(':') != 2:
                continue
            message, param, value = conf.split(':')
            message = self.replace_severity_values(message)
            self.configure[index] = f"{message}:{param}:{value}"

    def translate_patterns(self):
        self.include_patterns = self._translate_patterns(self.include)
        self.exclude_patterns = self._translate_patterns(self.exclude)

    def preparse(self, args):
        args = sys.argv[1:] if args is None else args
        parsed_args = []
        args = (arg for arg in args)
        for arg in args:
            if arg in ('-A', '--argumentfile'):
                try:
                    argfile = next(args)
                except StopIteration:
                    raise ArgumentFileNotFoundError('')
                parsed_args += self.load_args_from_file(argfile)
            else:
                parsed_args.append(arg)
        return parsed_args

    @staticmethod
    def load_args_from_file(argfile):
        try:
            with open(argfile) as arg_f:
                args = [arg for line in arg_f for arg in line.split()]
                if '-A' in args or '--argumentfile' in args:
                    raise NestedArgumentFileError(argfile)
                return args
        except FileNotFoundError:
            raise ArgumentFileNotFoundError(argfile)

    def _create_parser(self):
        # below will throw error in Pycharm, it's bug https://youtrack.jetbrains.com/issue/PY-41806
        parser = argparse.ArgumentParser(prog='robocop',
                                         formatter_class=argparse.RawTextHelpFormatter,
                                         description='Static code analysis tool for Robot Framework',
                                         epilog='For full documentation visit: '
                                                'https://github.com/MarketSquare/robotframework-robocop',
                                         add_help=False)
        required = parser.add_argument_group(title='Required parameters')
        optional = parser.add_argument_group(title='Optional parameters')

        required.add_argument('paths', metavar='paths', type=str, nargs='*', default=['.'], help=self.HELP_MSGS['help_paths'])

        optional.add_argument('-i', '--include', action=ParseDelimitedArgAction, default=self.include,
                              metavar='RULES', help=self.HELP_MSGS['help_include'])
        optional.add_argument('-e', '--exclude', action=ParseDelimitedArgAction, default=self.exclude,
                              metavar='RULES', help=self.HELP_MSGS['help_exclude'])
        optional.add_argument('-rules', '--ext_rules', action=ParseDelimitedArgAction, default=self.ext_rules,
                              help=self.HELP_MSGS['help_ext_rules'])
        optional.add_argument('--no-recursive', dest='recursive', action='store_false',
                              help=self.HELP_MSGS['help_recursive'])
        optional.add_argument('-r', '--reports', action=ParseDelimitedArgAction, default=self.reports,
                              help=self.HELP_MSGS['help_reports'])
        optional.add_argument('-f', '--format', type=str, default=self.format, help=self.HELP_MSGS['help_format'])
        optional.add_argument('-c', '--configure', action=ParseCheckerConfig, default=self.configure,
                              metavar='CONFIGURABLE', help=self.HELP_MSGS['help_configure'])
        optional.add_argument('-l', '--list', action=SetListOption, nargs='?', const='', default=self.list,
                              metavar='PATTERN', help=self.HELP_MSGS['help_list'])
        optional.add_argument('--list-configurables', action=SetListOption, nargs='?', const='', default=self.list_configurables,
                              metavar='PATTERN', help=self.HELP_MSGS['help_list_confs'])
        optional.add_argument('-o', '--output', type=argparse.FileType('w'), default=self.output,
                              metavar='PATH', help=self.HELP_MSGS['help_output'])
        optional.add_argument('--filetypes', action=ParseFileTypes, default=self.filetypes,
                              help=self.HELP_MSGS['help_filetypes'])
        optional.add_argument('-t', '--threshold', action=SetRuleThreshold, default=self.threshold,
                              help=self.HELP_MSGS['help_threshold'])
        optional.add_argument('-A', '--argumentfile', metavar='PATH', help=self.HELP_MSGS['help_argfile'])
        optional.add_argument('--ignore', action=ParseDelimitedArgAction, default=self.ignore,
                              metavar='PATH', help=self.HELP_MSGS['help_ignore'])
        optional.add_argument('-h', '--help', action='help', help=self.HELP_MSGS['help_info'])
        optional.add_argument('-v', '--version', action='version', version=__version__,
                              help=self.HELP_MSGS['help_version'])
        optional.add_argument('--directives', action='version', version=self.HELP_MSGS['directives'],
                              help=argparse.SUPPRESS)

        return parser

    def parse_opts(self, args=None):
        args = self.preparse(args)
        parsed_args = self.parser.parse_args(args)
        self.__dict__.update(**vars(parsed_args))
        self.remove_severity()
        self.translate_patterns()

        return parsed_args

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

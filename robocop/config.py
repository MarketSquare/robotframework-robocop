import os
import argparse
import re
import fnmatch
import sys

from robocop.version import __version__
from robocop.rules import RuleSeverity
from robocop.exceptions import ArgumentFileNotFoundError, NestedArgumentFileError


class ParseDelimitedArgAction(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        container = getattr(namespace, self.dest)
        container.update(values.split(','))


class ParseCheckerConfig(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        container = getattr(namespace, self.dest)
        container.append(values)


class ParseFileTypes(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        filetypes = getattr(namespace, self.dest)
        for filetype in values.split(','):
            filetypes.add(filetype if filetype.startswith('.') else '.' + filetype)
        setattr(namespace, self.dest, filetypes)


class SetMessageThreshold(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        for sev in RuleSeverity:
            if sev.value == values:
                break
        else:
            sev = RuleSeverity.INFO
        setattr(namespace, self.dest, sev)


class Config:
    def __init__(self):
        self.exec_dir = os.path.abspath('.')
        self.include = set()
        self.exclude = set()
        self.reports = {'return_status'}
        self.threshold = RuleSeverity.INFO
        self.configure = []
        self.format = "{source}:{line}:{col} [{severity}] {rule_id} {desc}"
        self.paths = []
        self.ext_rules = set()
        self.include_patterns = []
        self.exclude_patterns = []
        self.filetypes = {'.robot', '.resource'}
        self.list = False
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
        'help_reports':     'Run reports',
        'help_format':      'Format of output message. '
                            'You can use placeholders to change the way an issue is reported.\n'
                            'Default: {source}:{line}:{col} [{severity}] {rule_id} {desc}',
        'help_configure':   'Configure checker with parameter value. Usage:\n'
                            '-c message_name_or_id:param_name:param_value\nExample:\n'
                            '-c line-too-long:line_length:150\n'
                            '--configure 0101:severity:E',
        'help_list':        'List all available rules',
        'help_output':      'Path to output file',
        'help_filetypes':   'Comma separated list of file extensions to be scanned by Robocop',
        'help_threshold':    f'Disable rules below given threshold. Available message levels: '
                             f'{" < ".join(sev.value for sev in RuleSeverity)}',
        'help_recursive':   'Use this flag to stop scanning directories recursively',
        'help_argfile':     'Path to file with arguments',
        'help_info':        'Print this help message and exit',
        'help_version':     'Display Robocop version'
    }

    @staticmethod
    def _translate_pattern(pattern_list):
        return [re.compile(fnmatch.translate(p)) for p in pattern_list if '*' in p]

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
        self.include_patterns = self._translate_pattern(self.include)
        self.exclude_patterns = self._translate_pattern(self.exclude)

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

    def load_args_from_file(self, argfile):
        try:
            with open(argfile) as f:
                args = [arg for line in f for arg in line.split()]
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
                                                'https://github.com/bhirsz/robotframework-robocop',
                                         add_help=False)
        required = parser.add_argument_group(title='Required parameters')
        optional = parser.add_argument_group(title='Optional parameters')

        required.add_argument('paths', metavar='paths', type=str, nargs='*', help=self.HELP_MSGS['help_paths'])

        optional.add_argument('-i', '--include', action=ParseDelimitedArgAction, default=self.include,
                              help=self.HELP_MSGS['help_include'])
        optional.add_argument('-e', '--exclude', action=ParseDelimitedArgAction, default=self.exclude,
                              help=self.HELP_MSGS['help_exclude'])
        optional.add_argument('-rules', '--ext_rules', action=ParseDelimitedArgAction, default=self.ext_rules,
                              help=self.HELP_MSGS['help_ext_rules'])
        optional.add_argument('--no-recursive', dest='recursive', action='store_false',
                              help=self.HELP_MSGS['help_recursive'])
        optional.add_argument('-r', '--reports', action=ParseDelimitedArgAction, default=self.reports,
                              help=self.HELP_MSGS['help_reports'])
        optional.add_argument('-f', '--format', type=str, default=self.format, help=self.HELP_MSGS['help_format'])
        optional.add_argument('-c', '--configure', action=ParseCheckerConfig, default=self.configure,
                              help=self.HELP_MSGS['help_configure'])
        optional.add_argument('-l', '--list', action='store_true', default=self.list,
                              help=self.HELP_MSGS['help_list'])
        optional.add_argument('-o', '--output', type=argparse.FileType('w'), default=self.output,
                              help=self.HELP_MSGS['help_output'])
        optional.add_argument('--filetypes', action=ParseFileTypes, default=self.filetypes,
                              help=self.HELP_MSGS['help_filetypes'])
        optional.add_argument('-t', '--threshold', action=SetMessageThreshold, default=self.threshold,
                              help=self.HELP_MSGS['help_threshold'])
        optional.add_argument('-A', '--argumentfile', help=self.HELP_MSGS['help_argfile'])
        optional.add_argument('-h', '--help', action='help', help=self.HELP_MSGS['help_info'])
        optional.add_argument('-v', '--version', action='version', version=__version__,
                              help=self.HELP_MSGS['help_version'])
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


    @staticmethod
    def replace_severity_values(message):
        sev = ''.join(c.value for c in RuleSeverity)
        if re.match(f"[{sev}]?[0-9]{{4,}}", message):
            for c in sev:
                message = message.replace(c, '')
        return message

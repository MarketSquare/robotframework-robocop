import os
import argparse
import re
import fnmatch

from robocop.version import __version__


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
        filetypes = set()
        for filetype in values.split(','):
            filetypes.add(filetype if filetype.startswith('.') else '.' + filetype)
        setattr(namespace, self.dest, filetypes)


class Config:
    def __init__(self):
        self.exec_dir = os.path.abspath('.')
        self.include = set()
        self.exclude = set()
        self.reports = set()
        self.configure = []
        self.format = "{source}:{line}:{col} [{severity}] {msg_id} {desc}"
        self.paths = []
        self.include_patterns = []
        self.exclude_patterns = []
        self.filetypes = {'.robot', '.resource'}
        self.list = False
        self.output = None
        self.parser = self._create_parser()

    HELP_MSGS = {
        'help_paths':       'List of paths (files or directories) to be parsed by Robocop',
        'help_include':     'Run Robocop only with specified rules. You can define rule by its name or id',
        'help_exclude':     'Ignore specified rules. You can define rule by its name or id',
        'help_reports':     'Run reports',
        'help_format':      'Format of output message. '
                            'You can use placeholders to change the way an issue is reported. '
                            'Default: {source}:{line}:{col} [{severity}] {msg_id} {desc}',
        'help_configure':   'Configure checker with parameter value',
        'help_list':        'List all available rules',
        'help_output':      'Path to output file',
        'help_filetypes':   'Comma separated list of file extensions to be scanned by Robocop',
        'help_info':        'Print this help message and exit',
        'help_version':     'Display Robocop version'
    }

    @staticmethod
    def _translate_pattern(pattern_list):
        return [re.compile(fnmatch.translate(p)) for p in pattern_list if '*' in p]

    def translate_patterns(self):
        self.include_patterns = self._translate_pattern(self.include)
        self.exclude_patterns = self._translate_pattern(self.exclude)

    def _create_parser(self):
        parser = argparse.ArgumentParser(prog='robocop',
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
        optional.add_argument('-h', '--help', action='help', help=self.HELP_MSGS['help_info'])
        optional.add_argument('-v', '--version', action='version', version=__version__,
                              help=self.HELP_MSGS['help_version'])
        return parser

    def parse_opts(self, args=None):
        parsed_args = self.parser.parse_args(args)
        self.__dict__.update(**vars(parsed_args))
        self.translate_patterns()

        return parsed_args

    def is_rule_enabled(self, msg):
        if self.include and not self.include_patterns:
            if msg.msg_id not in self.include and msg.name not in self.include:
                return False
        if msg.msg_id in self.exclude or msg.name in self.exclude:
            return False
        for pattern in self.include_patterns:
            if not pattern.match(msg.msg_id) and not pattern.match(msg.name):
                return False
        for pattern in self.exclude_patterns:
            if pattern.match(msg.msg_id) or pattern.match(msg.name):
                return False
        return True

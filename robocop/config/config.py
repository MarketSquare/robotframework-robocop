import argparse
import re
import fnmatch


class ParseDelimetedArgAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        container = getattr(namespace, self.dest)
        container.update(values.split(','))


class ParseCheckerConfig(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        container = getattr(namespace, self.dest)
        container.append(values)


class Config:
    def __init__(self):
        self.include = set()
        self.exclude = set()
        self.reports = set()
        self.configure = list()
        self.format = "{source}:{line}:{col} [{severity}] {msg_id} {desc}"
        self.paths = []
        self.include_patterns = None
        self.exclude_patterns = None

    @staticmethod
    def _translate_pattern(pattern_list):
        return [re.compile(fnmatch.translate(p)) for p in pattern_list if '*' in p]

    def translate_patterns(self):
        self.include_patterns = self._translate_pattern(self.include)
        self.exclude_patterns = self._translate_pattern(self.exclude)

    def parse_opts(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-i', '--include', action=ParseDelimetedArgAction, default=self.include,
                            help='Run Robocop only with specified rules. You can define rule by its name or id')
        parser.add_argument('-e', '--exclude', action=ParseDelimetedArgAction, default=self.exclude,
                            help='Ignore specified rules. You can define rule by its name or id')
        parser.add_argument('-r', '--reports', action=ParseDelimetedArgAction, default=self.reports,
                            help='Run reports')
        parser.add_argument('-f', '--format', type=str, help='Format of output message', default=self.format)
        parser.add_argument('-c', '--configure', action=ParseCheckerConfig, default=self.configure,
                            help="Configure checker with parameter value")
        parser.add_argument('paths', metavar='paths', type=str, nargs='+',
                            help='List of paths (files and directories) to be parsed by Robocop')
        args = parser.parse_args()
        self.__dict__.update(**vars(args))
        self.translate_patterns()

    def is_rule_enabled(self, msg):
        if self.include and not self.include_patterns:
            if msg.msg_id not in self.include and msg.name not in self.include:
                return False
        if self.exclude:
            if msg.msg_id in self.exclude or msg.name in self.exclude:
                return False
        if self.include_patterns:
            for pattern in self.include_patterns:
                if not pattern.match(msg.msg_id) and not pattern.match(msg.name):
                    return False
        if self.exclude_patterns:
            for pattern in self.exclude_patterns:
                if pattern.match(msg.msg_id) or pattern.match(msg.name):
                    return False
        return True

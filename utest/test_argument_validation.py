import io
import unittest
import pathlib
from io import StringIO
from unittest.mock import patch
from robocop.config import Config
from robocop.version import __version__


class TestArgumentValidation(unittest.TestCase):
    def setUp(self):
        self.config = Config()

    def test_prog_name(self):
        self.assertEqual(self.config.parser.prog, 'robocop')

    def test_parser_default_help_disabled(self):
        self.assertFalse(self.config.parser.add_help)

    def test_default_args(self):
        self.assertSetEqual(self.config.filetypes, {'.resource', '.robot'})
        self.assertSetEqual(self.config.include, set())
        self.assertSetEqual(self.config.exclude, set())
        self.assertSetEqual(self.config.reports, set())
        self.assertListEqual(self.config.configure, [])
        self.assertEqual(self.config.format, "{source}:{line}:{col} [{severity}] {msg_id} {desc}")
        self.assertListEqual(self.config.paths, [])
        self.assertIsNone(self.config.output)

    def test_default_args_after_parse(self):
        args = self.config.parse_opts([''])
        self.assertSetEqual(args.filetypes, {'.resource', '.robot'})
        self.assertSetEqual(args.include, set())
        self.assertSetEqual(args.exclude, set())
        self.assertSetEqual(args.reports, set())
        self.assertListEqual(args.configure, [])
        self.assertEqual(args.format, "{source}:{line}:{col} [{severity}] {msg_id} {desc}")
        self.assertListEqual(args.paths, [''])
        self.assertIsNone(args.output)

    def test_filetypes_overwrite_defaults(self):
        args = self.config.parse_opts(['--filetypes', 'txt', ''])
        self.assertSetEqual(args.filetypes, {'.txt'})

    def test_filetypes_duplicate_defaults(self):
        args = self.config.parse_opts(['--filetypes', 'robot,resource', ''])
        self.assertSetEqual(args.filetypes, {'.resource', '.robot'})

    def test_filetypes_duplicate_dot_prefixed_defaults(self):
        args = self.config.parse_opts(['--filetypes', '.robot,.resource', ''])
        self.assertSetEqual(args.filetypes, {'.resource', '.robot'})

    def test_include_one_rule(self):
        rule_name = 'missing-keyword-doc'
        args = self.config.parse_opts(['--include', rule_name, ''])
        self.assertSetEqual(args.include, {rule_name})

    def test_include_two_same_rules_comma_separated(self):
        rule_name = 'missing-keyword-doc'
        args = self.config.parse_opts(['--include', ','.join([rule_name, rule_name]), ''])
        self.assertSetEqual(args.include, {rule_name})

    def test_include_two_same_rules_provided_separately(self):
        rule_name = 'missing-keyword-doc'
        args = self.config.parse_opts(['--include', rule_name, '--include', rule_name, ''])
        self.assertSetEqual(args.include, {rule_name})

    def test_include_two_different_rules_comma_separated(self):
        rule_name1 = 'missing-keyword-doc'
        rule_name2 = 'invalid-char-in-name'
        rules_names = ','.join([rule_name1, rule_name2])
        args = self.config.parse_opts(['--include', rules_names, ''])
        self.assertSetEqual(args.include, {rule_name1, rule_name2})

    def test_include_two_different_rules_provided_separately(self):
        rule_name1 = 'missing-keyword-doc'
        rule_name2 = 'invalid-char-in-name'
        args = self.config.parse_opts(['--include', rule_name1, '--include', rule_name2, ''])
        self.assertSetEqual(args.include, {rule_name1, rule_name2})

    def test_exclude_one_rule(self):
        rule_name = 'missing-keyword-doc'
        args = self.config.parse_opts(['--exclude', rule_name, ''])
        self.assertSetEqual(args.exclude, {rule_name})

    def test_exclude_two_same_rules_comma_separated(self):
        rule_name = 'missing-keyword-doc'
        args = self.config.parse_opts(['--exclude', ','.join([rule_name, rule_name]), ''])
        self.assertSetEqual(args.exclude, {rule_name})

    def test_exclude_two_same_rules_provided_separately(self):
        rule_name = 'missing-keyword-doc'
        args = self.config.parse_opts(['--exclude', rule_name, '--exclude', rule_name, ''])
        self.assertSetEqual(args.exclude, {rule_name})

    def test_exclude_two_different_rules_comma_separated(self):
        rule_name1 = 'missing-keyword-doc'
        rule_name2 = 'invalid-char-in-name'
        rules_names = ','.join([rule_name1, rule_name2])
        args = self.config.parse_opts(['--exclude', rules_names, ''])
        self.assertSetEqual(args.exclude, {rule_name1, rule_name2})

    def test_exclude_two_different_rules_provided_separately(self):
        rule_name1 = 'missing-keyword-doc'
        rule_name2 = 'invalid-char-in-name'
        args = self.config.parse_opts(['--exclude', rule_name1, '--exclude', rule_name2, ''])
        self.assertSetEqual(args.exclude, {rule_name1, rule_name2})

    def test_format_overwrite_default(self):
        default_format = '{source}:{line}:{col} [{severity}] {msg_id} {desc}'
        args = self.config.parse_opts(['--format', default_format, ''])
        self.assertEqual(args.format, default_format)

    def test_format_empty(self):
        empty_format = ''
        args = self.config.parse_opts(['--format', empty_format, ''])
        self.assertEqual(args.format, '')

    def test_format_new_value(self):
        new_format = '{source}: {msg_id} {desc}'
        args = self.config.parse_opts(['--format', new_format, ''])
        self.assertEqual(args.format, new_format)

    def test_output_new_value(self):
        args = self.config.parse_opts(['--output', 'results', ''])
        self.assertIsNotNone(args.output)
        self.assertIsInstance(args.output, io.TextIOWrapper)
        self.assertEqual(args.output.name, 'results')
        self.assertEqual(args.output.mode, 'w')
        self.assertTrue(pathlib.Path('results').exists())
        # pathlib.Path('results').unlink()
        # TODO remove 'results' file in cleanup and handle ResourceWarning

    @patch('sys.stdout', new_callable=StringIO)
    def test_help_message(self, mock_stdout):
        with self.assertRaises(SystemExit):
            self.config.parse_opts(['-h'])
        self.assertRegex(mock_stdout.getvalue(), r'usage:')

    @patch('sys.stdout', new_callable=StringIO)
    def test_help_message_long(self, mock_stdout):
        with self.assertRaises(SystemExit):
            self.config.parse_opts(['--help'])
        self.assertRegex(mock_stdout.getvalue(), r'usage:')

    @patch('sys.stdout', new_callable=StringIO)
    def test_version_number(self, mock_stdout):
        with self.assertRaises(SystemExit):
            self.config.parse_opts(['-v'])
        self.assertRegex(mock_stdout.getvalue(), __version__)

    @patch('sys.stdout', new_callable=StringIO)
    def test_version_number_long(self, mock_stdout):
        with self.assertRaises(SystemExit):
            self.config.parse_opts(['--version'])
        self.assertRegex(mock_stdout.getvalue(), __version__)

    @patch('sys.stderr', new_callable=StringIO)
    def test_paths_empty(self, mock_stderr):
        with self.assertRaises(SystemExit):
            self.config.parse_opts([])
        self.assertRegex(mock_stderr.getvalue(), r'error: the following arguments are required: paths')

    def test_paths_new_value(self):
        args = self.config.parse_opts(['tests.robot'])
        self.assertListEqual(args.paths, ['tests.robot'])

    def test_paths_two_values(self):
        args = self.config.parse_opts(['tests.robot', 'test2.robot'])
        self.assertListEqual(args.paths, ['tests.robot', 'test2.robot'])


if __name__ == '__main__':
    unittest.main()

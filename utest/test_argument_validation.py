import os
import unittest
from robocop.config import Config


class TestArgumentValidation(unittest.TestCase):
    def setUp(self):
        self.config = Config()

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

    def test_default_args(self):
        self.assertSetEqual(self.config.filetypes, {'.resource', '.robot'})
        self.assertSetEqual(self.config.include, set())
        self.assertSetEqual(self.config.exclude, set())
        self.assertSetEqual(self.config.reports, set())
        self.assertListEqual(self.config.configure, [])
        self.assertEqual(self.config.format, "{source}:{line}:{col} [{severity}] {msg_id} {desc}")
        self.assertListEqual(self.config.paths, [])
        self.assertIsNone(self.config.output)

    def test_add_filetype(self):
        args = self.config.parse_opts(['--filetypes', 'txt', ''])
        self.assertSetEqual(args.filetypes, {'.resource', '.robot', '.txt'})

    def test_duplicate_default_filetypes(self):
        args = self.config.parse_opts(['--filetypes', 'robot,resource', ''])
        self.assertSetEqual(args.filetypes, {'.resource', '.robot'})

    def test_duplicate_dot_prefixed_default_filetypes(self):
        args = self.config.parse_opts(['--filetypes', '.robot,.resource', ''])
        self.assertSetEqual(args.filetypes, {'.resource', '.robot'})

    def test_default_filetypes(self):
        args = self.config.parse_opts([''])
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

    def test_overwrite_default_format(self):
        default_format = '{source}:{line}:{col} [{severity}] {msg_id} {desc}'
        args = self.config.parse_opts(['--format', default_format, ''])
        self.assertEqual(args.format, default_format)

    def test_empty_format(self):
        empty_format = ''
        args = self.config.parse_opts(['--format', empty_format, ''])
        self.assertEqual(args.format, '')

    def test_new_format(self):
        new_format = '{source}: {msg_id} {desc}'
        args = self.config.parse_opts(['--format', new_format, ''])
        self.assertEqual(args.format, new_format)


if __name__ == '__main__':
    unittest.main()

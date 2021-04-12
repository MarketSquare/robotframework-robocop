""" General E2E tests to catch any general issue in robocop """
from pathlib import Path
import pytest
from robocop.exceptions import FileError, ArgumentFileNotFoundError, NestedArgumentFileError, ConfigGeneralError
from robocop.run import Robocop
from robocop.config import Config


@pytest.fixture
def robocop_instance():
    return Robocop(from_cli=True)


@pytest.fixture
def robocop_instance_not_cli():
    return Robocop(from_cli=False)


class TestE2E:
    def test_run_all_checkers(self, robocop_instance):
        config = Config()
        config.parse_opts([str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop_instance.config = config
        with pytest.raises(SystemExit):
            robocop_instance.run()

    def test_run_all_checkers_not_cli(self, robocop_instance_not_cli):
        robocop_instance_not_cli.config.paths = [str(Path(Path(__file__).parent.parent, 'test_data'))]
        issues = robocop_instance_not_cli.run()
        assert issues
        assert isinstance(issues[0], dict)

    def test_run_all_checkers_not_recursive(self, robocop_instance):
        config = Config()
        config.parse_opts(['--no-recursive',
                           str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop_instance.config = config
        with pytest.raises(SystemExit):
            robocop_instance.run()

    def test_all_reports(self, robocop_instance):
        config = Config()
        config.parse_opts([
            '-r',
            'all',
            str(Path(Path(__file__).parent.parent, 'test_data'))
        ])
        robocop_instance.config = config
        with pytest.raises(SystemExit):
            robocop_instance.run()

    def test_no_issues_all_reports(self, robocop_instance):
        config = Config()
        config.parse_opts([
            '-r',
            'all',
            str(Path(Path(__file__).parent.parent, 'test_data/all_passing.robot'))
        ])
        robocop_instance.config = config
        with pytest.raises(SystemExit):
            robocop_instance.run()

    def test_disable_all_pattern(self, robocop_instance):
        config = Config()
        config.parse_opts([
            '--exclude',
            '*',
            str(Path(Path(__file__).parent.parent, 'test_data'))
        ])
        robocop_instance.config = config
        with pytest.raises(SystemExit):
            robocop_instance.run()

    def test_ignore_file_with_pattern(self, robocop_instance):
        config = Config()
        config.parse_opts([
            '--ignore',
            '*.robot',
            '--include',
            '0502',
            str(Path(Path(__file__).parent.parent, 'test_data'))
        ])
        robocop_instance.config = config
        with pytest.raises(SystemExit):
            robocop_instance.run()

    def test_include_one_rule(self, robocop_instance):
        config = Config()
        config.parse_opts([
            '--include',
            '0503',
            str(Path(Path(__file__).parent.parent, 'test_data'))
        ])
        robocop_instance.config = config
        with pytest.raises(SystemExit):
            robocop_instance.run()

    def test_run_non_existing_file(self, robocop_instance):
        config = Config()
        config.parse_opts(['some_path'])
        robocop_instance.config = config
        with pytest.raises(FileError) as err:
            robocop_instance.run()
        assert 'File "some_path" does not exist' in str(err)

    def test_run_with_return_status_0(self, robocop_instance):
        config = Config()
        config.parse_opts(['-c', 'return_status:quality_gate:E=-1:W=-1',
                           str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop_instance.config = config
        with pytest.raises(SystemExit):
            robocop_instance.run()
        assert robocop_instance.reports['return_status'].return_status == 0

    def test_run_with_return_status_bigger_than_zero(self, robocop_instance):
        config = Config()
        config.parse_opts(['--configure', 'return_status:quality_gate:E=0:W=0',
                           str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop_instance.config = config
        with pytest.raises(SystemExit):
            robocop_instance.run()
        assert robocop_instance.reports['return_status'].return_status > 0

    def test_configure_rule_severity(self, robocop_instance):
        config = Config()
        config.parse_opts(['-c', '0201:severity:E,E0202:severity:I',
                           str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop_instance.config = config
        with pytest.raises(SystemExit):
            robocop_instance.run()

    def test_configure_rule_option(self, robocop_instance):
        config = Config()
        config.parse_opts(['-c', 'line-too-long:line_length:1000',
                           str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop_instance.config = config
        with pytest.raises(SystemExit):
            robocop_instance.run()

    def test_configure_invalid_rule(self, robocop_instance):
        config = Config()
        config.parse_opts(['--configure', 'idontexist:severity:E',
                           str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop_instance.config = config
        robocop_instance.load_checkers()
        with pytest.raises(ConfigGeneralError) as err:
            robocop_instance.configure_checkers_or_reports()
        assert "Provided rule or report 'idontexist' does not exist" in str(err)

    def test_configure_invalid_param(self, robocop_instance):
        config = Config()
        config.parse_opts(['--configure', '0202:idontexist:E',
                           str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop_instance.config = config
        robocop_instance.load_checkers()
        with pytest.raises(ConfigGeneralError) as err:
            robocop_instance.configure_checkers_or_reports()
        assert r"Provided param 'idontexist' for rule '0202' does not exist. " \
               r"Available configurable(s) for this rule:\n    severity" in str(err)

    def test_configure_invalid_config(self, robocop_instance):
        config = Config()
        config.parse_opts(['--configure', '0202:',
                           str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop_instance.config = config
        robocop_instance.load_checkers()
        with pytest.raises(ConfigGeneralError) as err:
            robocop_instance.configure_checkers_or_reports()
        assert "Provided invalid config: '0202:' (general pattern: <rule>:<param>:<value>)" in str(err)

    def test_configure_return_status_invalid_value(self, robocop_instance):
        config = Config()
        config.parse_opts(['--configure', 'return_status:quality_gate:E0',
                           str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop_instance.config = config
        with pytest.raises(SystemExit):
            robocop_instance.run()

    def test_configure_return_status_with_non_exist(self, robocop_instance):
        config = Config()
        config.parse_opts(['--configure', 'return_status:smth:E=0:W=0',
                           str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop_instance.config = config
        robocop_instance.load_reports()
        with pytest.raises(ConfigGeneralError) as err:
            robocop_instance.configure_checkers_or_reports()
        assert "Provided param 'smth' for report 'return_status' does not exist" in str(err)

    def test_use_argument_file(self, robocop_instance):
        config = Config()
        config.parse_opts(['-A', str(Path(Path(__file__).parent.parent, 'test_data/argument_file/args.txt')),
                           str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop_instance.config = config
        with pytest.raises(SystemExit):
            robocop_instance.run()

    def test_use_not_existing_argument_file(self):
        config = Config()
        with pytest.raises(ArgumentFileNotFoundError) as err:
            config.parse_opts(['--argumentfile', 'some_file',
                               str(Path(Path(__file__).parent.parent, 'test_data'))])
        assert 'Argument file "some_file" does not exist' in str(err)

    def test_argument_file_without_path(self):
        config = Config()
        with pytest.raises(ArgumentFileNotFoundError) as err:
            config.parse_opts(['--argumentfile'])
        assert 'Argument file "" does not exist' in str(err)

    def test_use_nested_argument_file(self):
        config = Config()
        nested_args_path = str(Path(Path(__file__).parent.parent, 'test_data/argument_file/args_nested.txt'))
        with pytest.raises(NestedArgumentFileError) as err:
            config.parse_opts(['-A', nested_args_path,
                               str(Path(Path(__file__).parent.parent, 'test_data'))])
        assert 'Nested argument file in ' in str(err)

    def test_set_rule_threshold(self, robocop_instance):
        config = Config()
        config.parse_opts([
            '--threshold',
            'E',
            str(Path(Path(__file__).parent.parent, 'test_data'))
        ])
        robocop_instance.config = config
        with pytest.raises(SystemExit):
            robocop_instance.run()

    def test_set_rule_invalid_threshold(self, robocop_instance):
        config = Config()
        config.parse_opts([
            '--threshold',
            '3',
            str(Path(Path(__file__).parent.parent, 'test_data'))
        ])
        robocop_instance.config = config
        with pytest.raises(SystemExit):
            robocop_instance.run()

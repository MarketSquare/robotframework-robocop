""" General E2E tests to catch any general issue in robocop """
import os
from pathlib import Path
import pytest
from robocop.exceptions import FileError, ArgumentFileNotFoundError, NestedArgumentFileError, ConfigGeneralError
from robocop.run import Robocop
from robocop.config import Config


@pytest.fixture
def robocop():
    return Robocop()


class TestE2E:
    def test_run_all_checkers(self, robocop):
        config = Config()
        config.parse_opts([str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop.config = config
        with pytest.raises(SystemExit):
            robocop.run()

    def test_run_all_checkers_not_recursive(self, robocop):
        config = Config()
        config.parse_opts(['--no-recursive',
                           str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop.config = config
        with pytest.raises(SystemExit):
            robocop.run()

    def test_all_reports(self, robocop):
        config = Config()
        config.parse_opts([
            '-r',
            'rules_by_id,rules_by_error_type',
            str(Path(Path(__file__).parent.parent, 'test_data'))
        ])
        robocop.config = config
        with pytest.raises(SystemExit):
            robocop.run()

    def test_run_without_path(self, robocop, capsys):
        with pytest.raises(SystemExit):
            robocop.run()
        out, _ = capsys.readouterr()
        assert "No path has been provided" in str(out)

    def test_run_non_existing_file(self, robocop):
        config = Config()
        config.parse_opts(['some_path'])
        robocop.config = config
        with pytest.raises(FileError) as err:
            robocop.run()
        assert 'File some_path does not exist' in str(err)

    def test_run_with_return_status_0(self, robocop):
        config = Config()
        config.parse_opts(['-c', 'return_status:quality_gate:E=-1:W=-1',
                           str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop.config = config
        robocop.configure_checkers_or_reports()
        with pytest.raises(SystemExit):
            robocop.run()
        for report in robocop.reports:
            if report.name == 'return_status':
                assert report.return_status == 0

    def test_run_with_return_status_1(self, robocop):
        config = Config()
        config.parse_opts(['--configure', 'return_status:quality_gate:E=0:W=0',
                           str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop.config = config
        robocop.configure_checkers_or_reports()
        with pytest.raises(SystemExit):
            robocop.run()
        for report in robocop.reports:
            if report.name == 'return_status':
                assert report.return_status == 1

    def test_configure_rule_severity(self, robocop):
        config = Config()
        config.parse_opts(['-c', '0201:severity:E,E0202:severity:I',
                           str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop.config = config
        with pytest.raises(SystemExit):
            robocop.run()

    def test_configure_invalid_rule(self, robocop):
        config = Config()
        config.parse_opts(['--configure', 'idontexist:severity:E',
                           str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop.config = config
        with pytest.raises(ConfigGeneralError) as err:
            robocop.configure_checkers_or_reports()
        assert "Provided rule or report 'idontexist' does not exists" in str(err)

    def test_configure_invalid_param(self, robocop):
        config = Config()
        config.parse_opts(['--configure', '0202:idontexist:E',
                           str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop.config = config
        with pytest.raises(ConfigGeneralError) as err:
            robocop.configure_checkers_or_reports()
        assert "Provided param 'idontexist' for rule '0202' does not exists" in str(err)

    def test_configure_return_status_invalid_value(self, robocop):
        config = Config()
        config.parse_opts(['--configure', 'return_status:quality_gate:G=0',
                           str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop.config = config
        robocop.configure_checkers_or_reports()
        with pytest.raises(SystemExit):
            robocop.run()

    def test_configure_return_status_with_non_exist(self, robocop):
        config = Config()
        config.parse_opts(['--configure', 'return_status:smth:E=0:W=0',
                           str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop.config = config
        with pytest.raises(ConfigGeneralError) as err:
            robocop.configure_checkers_or_reports()
        assert "Provided param 'smth' for report 'return_status' does not exists"

    def test_use_argument_file(self, robocop):
        config = Config()
        config.parse_opts(['-A', str(Path(Path(__file__).parent.parent, 'test_data/argument_file/args.txt')),
                           str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop.config = config
        with pytest.raises(SystemExit):
            robocop.run()

    def test_use_not_existing_argument_file(self, robocop):
        config = Config()
        with pytest.raises(ArgumentFileNotFoundError) as err:
            config.parse_opts(['--argumentfile', 'some_file',
                               str(Path(Path(__file__).parent.parent, 'test_data'))])
        assert 'Argument file "some_file" does not exist' in str(err)

    def test_use_nested_argument_file(self, robocop):
        config = Config()
        nested_args_path = str(Path(Path(__file__).parent.parent, 'test_data/argument_file/args_nested.txt'))
        with pytest.raises(NestedArgumentFileError) as err:
            config.parse_opts(['-A', nested_args_path,
                               str(Path(Path(__file__).parent.parent, 'test_data'))])
        assert f'Nested argument file in ' in str(err)

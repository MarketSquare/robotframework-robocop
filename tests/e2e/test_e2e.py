""" General E2E tests to catch any general issue in robocop """
from pathlib import Path
import pytest
import robocop
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
        with pytest.raises(SystemExit) as err:
            robocop.run()

    def test_run_with_return_status_0(self, robocop):
        config = Config()
        config.parse_opts(['-c', 'return_status:quality_gate:E=-1:W=-1',
                           str(Path(Path(__file__).parent.parent, 'test_data'))])
        robocop.config = config
        robocop.configure_checkers_or_reports()
        with pytest.raises(SystemExit) as err:
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
        with pytest.raises(SystemExit) as err:
            robocop.run()
        for report in robocop.reports:
            if report.name == 'return_status':
                assert report.return_status == 1

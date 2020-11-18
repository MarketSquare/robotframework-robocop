from pathlib import Path
import pytest
import jinja2
from robocop.exceptions import FileError, ArgumentFileNotFoundError, NestedArgumentFileError, ConfigGeneralError
from robocop.run import Robocop
from robocop.config import Config


@pytest.fixture
def robocop_instance():
    return Robocop()


class TestPerformance:
    def test_create_and_scan_big_file(self, robocop_instance):
        template = jinja2.Environment(
            loader=jinja2.FileSystemLoader(Path(__file__).parent)
        ).get_template('big_file.template')
        with open('big_file.robot', 'w') as f:
            f.write(template.render())
        config = Config()
        config.parse_opts([str(Path(Path(__file__).parent, 'big_file.robot'))])
        robocop_instance.config = config
        with pytest.raises(SystemExit):
            robocop_instance.run()

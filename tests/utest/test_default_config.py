import os
import sys
from pathlib import Path
from unittest.mock import patch
import pytest
from robocop.config import Config


@pytest.fixture
def config():
    return Config()


class TestDefaultConfig:
    def test_find_project_root_same_dir(self, config):
        src = Path(__file__).parent.parent / 'test_data' / 'default_config'
        os.chdir(str(src))
        root = config.find_project_root()
        assert root == src

    def test_find_project_root_missing_but_git(self, config):
        src = Path(__file__).parent.parent / 'test_data' / 'default_config_missing' / 'nested' / 'deeper'
        expected_root = Path(__file__).parent.parent / 'test_data' / 'default_config_missing'
        os.chdir(str(src))
        root = config.find_project_root()
        assert root == expected_root

    def test_load_config_from_default_file(self, config):
        src = Path(__file__).parent.parent / 'test_data' / 'default_config'
        os.chdir(str(src))
        with patch.object(sys, 'argv', ['prog']):
            config.parse_opts()
        assert {'0810'} == config.include

    def test_ignore_config_from_default_file(self, config):
        src = Path(__file__).parent.parent / 'test_data' / 'default_config'
        os.chdir(str(src))
        with patch.object(sys, 'argv', ['prog', '--include', '0202']):
            config.parse_opts()
        assert {'0202'} == config.include

import textwrap
from pathlib import Path

import click
import pytest
import typer

from robocop.config.parser import read_toml_config
from robocop.config.schema import RawConfig
from tests import working_directory

DATA_DIR = Path(__file__).parent / "test_data"


def generate_config(config_path: Path, config_content: str) -> Path:
    config = textwrap.dedent(config_content)
    config_path.write_text(config)
    return config_path


class TestExtendConfig:
    def test_extend_config_physical_paths(self):
        # Arrange
        config_path = DATA_DIR / "extends" / "extend_physical.toml"
        # Act
        raw_config = RawConfig.from_dict(config_dict=read_toml_config(config_path), config_path=config_path)
        # Assert
        assert raw_config.config_source == str(config_path)
        assert raw_config.linter.persistent  # set in the base
        assert not raw_config.linter.silent  # overridden in the final config
        assert raw_config.linter.exit_zero  # only set in the final config
        assert raw_config.linter.select == ["ARG05", "line-too-long"]

    def test_extend_config_nested(self):
        # Arrange
        config_path = DATA_DIR / "extends" / "nested_extends.toml"
        # Act
        raw_config = RawConfig.from_dict(config_dict=read_toml_config(config_path), config_path=config_path)
        # Assert
        assert raw_config.config_source == str(config_path)
        assert raw_config.linter.persistent is True  # set in the base
        assert raw_config.linter.silent is True  # overridden in the final config
        assert raw_config.linter.exit_zero is True  # only set in the 2nd config
        assert raw_config.linter.select == ["ARG05", "line-too-long"]

    def test_empty_extends(self):
        # Arrange
        config_path = DATA_DIR / "extends" / "empty_extends.toml"
        # Act
        raw_config = RawConfig.from_dict(config_dict=read_toml_config(config_path), config_path=config_path)
        # Assert
        assert raw_config.config_source == str(config_path)
        assert raw_config.linter.select == ["line-too-long"]

    def test_generated_with_absolute_path(self, tmp_path):
        # Arrange
        base_config_path = generate_config(
            tmp_path / "base.toml",
            """
            [tool.robocop.lint]
            select = [
                "VAR01"
            ]
            configure = [
                "rule.param=value"
            ]
            """,
        )
        starting_config_path = generate_config(
            tmp_path / "starting_config.toml",
            f"""
            [tool.robocop]
            extends = ["{base_config_path.absolute().as_posix()}"]

            [tool.robocop.lint]
            select = [
                "VAR02"
            ]
            """,
        )
        # Act
        raw_config = RawConfig.from_dict(
            config_dict=read_toml_config(starting_config_path), config_path=starting_config_path
        )
        # Assert
        assert raw_config.config_source == str(starting_config_path)
        assert raw_config.linter.select == ["VAR01", "VAR02"]
        assert raw_config.linter.configure == ["rule.param=value"]

    def test_circular_extends(self, capsys):
        # Arrange
        config_path = DATA_DIR / "extends" / "circular.toml"
        # Act
        with pytest.raises(typer.Exit) as exit_status:
            read_toml_config(config_path)
        _, err = capsys.readouterr()
        normalized_err = "".join(err.splitlines())
        # Assert
        assert exit_status.value.exit_code == 2
        assert (
            f"Circular reference found in 'extends' parameter in the configuration file: {config_path}"
            in normalized_err
        )

    @pytest.mark.parametrize("config_name", ["extends_empty.toml", "extends_empty_valid_robocop.toml"])
    def test_extends_with_empty_config(self, config_name):
        # Arrange
        config_path = DATA_DIR / "extends" / config_name
        # Act
        raw_config = RawConfig.from_dict(config_dict=read_toml_config(config_path), config_path=config_path)
        # Assert
        assert raw_config.config_source == str(config_path)

    def test_invalid_toml_file(self):
        # Arrange
        config_path = DATA_DIR / "extends" / "invalid.toml"
        # Act
        with pytest.raises(click.FileError) as exc_info:
            read_toml_config(config_path)
        # Assert
        assert (
            "Error reading configuration file: Expected '=' after a key in a key/value pair" in exc_info.value.message
        )

    @pytest.mark.parametrize("invalid_extend", [1, []])
    def test_invalid_extends(self, invalid_extend, tmp_path, capsys):
        # Arrange
        config_path = generate_config(
            tmp_path / "invalid_extends.toml",
            f"""
            [tool.robocop]
            extends = [{invalid_extend}]
            """,
        )
        # Act
        with pytest.raises(typer.Exit) as exit_status:
            read_toml_config(config_path)
        _, err = capsys.readouterr()
        normalized_err = "".join(err.splitlines())
        # Assert
        assert exit_status.value.exit_code == 2
        assert "Invalid 'extends' parameter value in the configuration file:" in normalized_err
        assert str(config_path) in normalized_err
        assert f"{invalid_extend} is not a string." in normalized_err

    def test_inheritance_mro(self, tmp_path):
        # Arrange
        generate_config(
            tmp_path / "base.toml",
            """
            [tool.robocop.lint]
            select = ["DOC01"]
            """,
        )
        generate_config(
            tmp_path / "a.toml",
            """
            [tool.robocop]
            extends = ["base.toml"]
            """,
        )
        generate_config(
            tmp_path / "b.toml",
            """
            [tool.robocop]
            extends = ["base.toml"]
            """,
        )
        final_config = generate_config(
            tmp_path / "final.toml",
            """
            [tool.robocop]
            extends = ["a.toml", "b.toml"]
            """,
        )
        # Act
        with working_directory(tmp_path):
            raw_config = RawConfig.from_dict(config_dict=read_toml_config(final_config), config_path=final_config)
        # Assert
        assert raw_config.config_source == str(final_config)
        assert raw_config.linter.select == ["DOC01", "DOC01"]

    def test_not_toml_are_ignored(self):
        # Arrange
        config_path = DATA_DIR / "extends" / "extends_with_name.toml"
        # Act
        raw_config = RawConfig.from_dict(config_dict=read_toml_config(config_path), config_path=config_path)
        # Assert
        assert raw_config.config_source == str(config_path)
        assert raw_config.linter is None

    def test_extend_does_not_exist(self, tmp_path):
        # Arrange
        config_path = generate_config(
            tmp_path / "with_not_existing.toml",
            """
            [tool.robocop]
            extends = ["notexist.toml"]
            """,
        )
        # Act
        with pytest.raises(click.FileError) as exc_info:
            read_toml_config(config_path)
        # Assert
        assert "Error reading configuration file: [Errno 2] No such file or directory:" in exc_info.value.message

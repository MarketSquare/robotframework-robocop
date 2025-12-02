# TODO: also test rules docs. For example write rules docs to file and then extract
import re
import shlex
import subprocess
import textwrap
from pathlib import Path
from typing import Callable

import pytest
from typer import Exit

from robocop.run import check_files, format_files
from tests import working_directory

DOCS_DIR = Path(__file__).parent.parent.parent / "docs"

EXAMPLE_ROBOT = """
*** Settings ***
Documentation    This is example file


*** Test Cases ***
Example test case
    [Documentation]    Example documentation
    Log    Example log message    console=True
"""
EXAMPLE_CONFIG = """
[tool.robocop]
verbose = false
"""


@pytest.fixture(scope="session")
def tmp_robot_dir(tmp_path_factory):
    """
    Create a temporary directory with example files.

    Cli commands use example files in the documentation.
    For example, if documentation contains a command:

        robocop check --config robocop/config.toml

    We need to ensure that our test environment contains the following files.
    """
    tmp_path = tmp_path_factory.mktemp("tmp_robot_dir")
    files = {
        tmp_path / "golden.robot": "",
        tmp_path / "test.txt": "",
        tmp_path / "example.robot": "",
        tmp_path / "test.robot": "",
        tmp_path / "robocop" / "config.toml": EXAMPLE_CONFIG.lstrip(),
        tmp_path / "path" / "to" / "config.toml": EXAMPLE_CONFIG.lstrip(),
        tmp_path / "custom_rules.py": "",
        tmp_path / "CustomFormatter.py": "",
        tmp_path / "my" / "own" / "rule.py": "",
        tmp_path / "my" / "own" / "Formatter.py": "",
    }
    empty_directories = [
        tmp_path / "resources" / "etc",
        tmp_path / "path" / "to" / "project" / "root",
        tmp_path / "tests",
        tmp_path / "bdd",
    ]
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    for directory in empty_directories:
        directory.mkdir(parents=True, exist_ok=True)

    return tmp_path


def trim_code_block(code: str) -> str:
    return textwrap.dedent(code).lstrip(" ")


def get_code_blocks(languages: list[str]) -> dict[str, list[str]]:
    languages_str = "|".join(languages)
    code_block_pattern = re.compile(
        rf"```\s?{languages_str}.*?\n(.*?)(?=\s+```)", re.DOTALL | re.IGNORECASE | re.MULTILINE
    )
    code_blocks = {}
    for md in DOCS_DIR.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        matches = code_block_pattern.findall(text)
        blocks = [trim_code_block(code) for code in matches]
        if blocks:
            code_blocks[md] = blocks
    return code_blocks


def create_config_file(code: str, path: Path) -> None:
    if "template.jinja" in code:
        print()
    path.write_text(code, encoding="utf-8")


def run_cmd(cmd: Callable, config_path: Path, config: str, **kwargs) -> None:
    try:
        cmd(configuration_file=config_path, **kwargs)
    except Exit as err:
        if err.exit_code != 0:
            pytest.fail(
                f"Failed to run Robocop with config file {config_path}. Config file:\n{config}\n\nError:\n{err}"
            )
    except Exception as err:  # noqa: BLE001
        pytest.fail(f"Failed to run Robocop with config file {config_path}. Config file:\n{config}\n\nError:\n{err}")


@pytest.mark.docs
def test_toml_config(tmp_robot_dir):
    blocks = get_code_blocks(["toml"])
    config_path = tmp_robot_dir / "robot.toml"
    for configs in blocks.values():
        for config in configs:
            if "CustomFormatters" in config:
                continue
            if "GenerateDocumentation.doc_template" in config:
                continue
            create_config_file(config, config_path)
            with working_directory(tmp_robot_dir):
                run_cmd(check_files, config_path, config, root=tmp_robot_dir, exit_zero=True)
                run_cmd(format_files, config_path, config, root=tmp_robot_dir)


@pytest.mark.docs
def test_cli_config(tmp_robot_dir):
    (tmp_robot_dir / "robot.toml").unlink(missing_ok=True)
    blocks = get_code_blocks(["bash"])
    seen = set()
    for configs in blocks.values():
        # configs = [one_line.lstrip() for config in configs for one_line in config.split("\n")]
        for config in configs:
            if "pip" in config:
                continue
            if config.startswith(">"):
                config = [config.split("\n")[0][1:]]
            else:
                config = config.split("\n")
            for conf in config:
                conf = conf.lstrip()
                conf = conf.split("#")[0]  # remove comments
                if not conf or conf in seen:
                    continue
                seen.add(conf)
                print(f"Running command: {conf}")
                with working_directory(tmp_robot_dir):
                    if "robocop check" in conf:
                        conf = f"{conf} --exit-zero"
                    if "--persistent" in conf:  # TODO: requires system cache
                        continue
                    if "--install-completion" in conf:  # TODO: not supported in subprocess
                        continue
                    if "--extend-select CustomFormatters" in conf:  # TODO: need to prepare the whole test module
                        continue
                    if "GenerateDocumentation.doc_template" in conf:
                        continue
                    subprocess.run(shlex.split(conf), check=True)  # noqa: S603

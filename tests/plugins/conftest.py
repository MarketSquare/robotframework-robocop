from __future__ import annotations

import sys
from pathlib import Path

import pytest

from robocop import plugins
from robocop.linter.rules import RuleSeverity
from robocop.runtime.resolver import RuleMatcher, RulesLoader
from robocop.version_handling import ROBOT_VERSION

TEST_DATA_DIR = Path(__file__).parent / "test_data"
PLUGIN_SITE_DIR = TEST_DATA_DIR / "example_plugin"


def _purge_plugin_modules() -> None:
    for module in list(sys.modules):
        if module == "example_plugin" or module.startswith("example_plugin."):
            del sys.modules[module]


@pytest.fixture
def example_plugin():
    """
    Register the example plugin without installing it.

    ``importlib.metadata`` discovers entry points by scanning ``sys.path`` for ``*.dist-info`` directories,
    so putting the directory with the plugin package and its metadata on ``sys.path`` is enough.
    """
    sys.path.insert(0, str(PLUGIN_SITE_DIR))
    plugins.get_plugins.cache_clear()
    try:
        yield plugins.get_plugins()
    finally:
        sys.path.remove(str(PLUGIN_SITE_DIR))
        plugins.get_plugins.cache_clear()
        _purge_plugin_modules()


@pytest.fixture
def no_plugins():
    """Make sure no Robocop plugin is discovered."""
    plugins.get_plugins.cache_clear()
    try:
        yield
    finally:
        plugins.get_plugins.cache_clear()


@pytest.fixture
def loader() -> RulesLoader:
    rule_matcher = RuleMatcher(
        select=[],
        extend_select=[],
        ignore=[],
        target_version=ROBOT_VERSION,
        threshold=RuleSeverity.INFO,
        fixable=[],
        unfixable=[],
    )
    return RulesLoader(rule_matcher=rule_matcher, custom_rules=[], configure=[], silent=True, config_source="mock")

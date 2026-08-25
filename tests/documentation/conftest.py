import os
import sys
from pathlib import Path

import pytest

from robocop import plugins

PLUGIN_SITE_DIR = Path(__file__).parent.parent / "plugins" / "test_data" / "example_plugin"


def pytest_collection_modifyitems(config, items):
    if config.getoption("-m") != "docs":
        skip_docs = pytest.mark.skip(reason="run with -m docs to execute")
        for item in items:
            if "docs" in item.keywords:
                item.add_marker(skip_docs)


@pytest.fixture(autouse=True, scope="session")
def example_plugin_installed():
    """
    Register the example plugin used in the plugin documentation.

    Documentation examples reference the ``example`` plugin. Putting the directory with the plugin package and
    its metadata on ``sys.path`` (and ``PYTHONPATH``, for the examples executed in a subprocess) is enough for
    ``importlib.metadata`` to discover it.
    """
    plugin_dir = str(PLUGIN_SITE_DIR)
    previous_python_path = os.environ.get("PYTHONPATH")
    sys.path.insert(0, plugin_dir)
    os.environ["PYTHONPATH"] = os.pathsep.join(filter(None, [plugin_dir, previous_python_path]))
    plugins.get_plugins.cache_clear()
    try:
        yield
    finally:
        sys.path.remove(plugin_dir)
        if previous_python_path is None:
            del os.environ["PYTHONPATH"]
        else:
            os.environ["PYTHONPATH"] = previous_python_path
        plugins.get_plugins.cache_clear()

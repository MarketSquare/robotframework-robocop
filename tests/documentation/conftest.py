import pytest


def pytest_collection_modifyitems(config, items):
    if config.getoption("-m") != "docs":
        skip_docs = pytest.mark.skip(reason="run with -m docs to execute")
        for item in items:
            if "docs" in item.keywords:
                item.add_marker(skip_docs)

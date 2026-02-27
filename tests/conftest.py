from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from robocop.config.builder import ConfigBuilder

if TYPE_CHECKING:
    from robocop.config.schema import Config

# We are appending tests directory to sys path so we can use tests utils inside tests
sys.path.append(str(Path(__file__).parent.parent))


@pytest.fixture
def empty_config() -> Config:
    return ConfigBuilder().from_raw(None, None)

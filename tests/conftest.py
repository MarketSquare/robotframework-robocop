# We are appending tests directory to sys path so we can use tests utils inside tests

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

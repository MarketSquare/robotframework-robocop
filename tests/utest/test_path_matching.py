from pathlib import Path

from robocop.files import get_files
from robocop.config import Config


class TestPathMatching:
    def test_paths_from_gitignore_ignored(self):
        test_dir = Path(__file__).parent.parent / "test_data" / "gitignore"
        config = Config()
        config.paths = {str(test_dir)}
        files = list(get_files(config))
        assert sorted(files) == [test_dir / "allowed" / "allowed_file.robot", test_dir / "allowed_file.robot"]

from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_rf6.1.txt", test_on_version=">=6.1")

    def test_rf6(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_rf6.txt", test_on_version="==6.0")

    def test_rf5(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_rf5.txt", test_on_version="==5.*")

    def test_rf4(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_rf4.txt", test_on_version="==4.*")

    def test_extended(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
            test_on_version=">=6.1",
        )

    # TODO: Relative paths with symlinks that also work with config paths
    # For example keep paths in a object that keep original non resolved path
    # import sys
    # from pathlib import Path
    #
    # import pytest
    #
    # from tests import working_directory
    # @pytest.mark.skipif(sys.platform != "linux", reason="Test only runs on Linux")
    # def test_with_symlink(self, tmp_path):
    #     absolute_path = Path(__file__).parent / "test.robot"
    #     (tmp_path / "test.robot").symlink_to(absolute_path)
    #     with working_directory(tmp_path):
    #         self.check_rule(
    #             src_files=["test.robot"],
    #             expected_file="expected_output_rf6.1.txt",
    #             test_on_version=">=6.1",
    #             test_dir=tmp_path,
    #         )

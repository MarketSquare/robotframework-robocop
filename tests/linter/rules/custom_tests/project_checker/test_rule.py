from pathlib import Path

from tests.linter.utils import RuleAcceptance

CUR_DIR = Path(__file__).parent


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["."],
            expected_file="expected_output.txt",
            config=f"--ext-rules {CUR_DIR}/external_project_checker -i project-checker,test-total-count",
        )

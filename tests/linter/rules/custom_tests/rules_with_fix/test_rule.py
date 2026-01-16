from pathlib import Path

from tests.linter.utils import RuleAcceptance

CUR_DIR = Path(__file__).parent


class TestRuleAcceptance(RuleAcceptance):
    def test_fix(self):
        self.check_rule_fix(
            src_files=["test.robot"],
            expected_dir="expected_fixed",
            select=["fixable-rule"],
            custom_rules=[f"{CUR_DIR}/custom_rules.py"],
        )

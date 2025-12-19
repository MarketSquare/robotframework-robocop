from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt", test_on_version=">=7.2")

    def test_rule_rf4(self):
        self.check_rule(src_files=["test_rf4.robot"], expected_file="expected_output_rf4.txt", test_on_version="<7.2")

    def test_extended(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
            test_on_version=">=7.2",
        )

    def test_custom_markers(self):
        self.check_rule(
            configure=["commented-out-code.markers=todo,fixme,note,skip"],
            src_files=["custom_markers/test.robot"],
            expected_file="custom_markers/expected_output.txt",
        )

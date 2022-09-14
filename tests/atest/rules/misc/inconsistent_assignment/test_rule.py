from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["golden/golden.robot"], expected_file=None)

    def test_configured_const_assignment(self):
        self.check_rule(
            config="-c inconsistent-assignment:assignment_sign_type:space_and_equal_sign",
            src_files=["const/test.robot"],
            expected_file="const/expected_output.txt",
        )

    def test_autodetect(self):
        self.check_rule(
            config="-c inconsistent-assignment:assignment_sign_type:autodetect",
            src_files=["autodetect/test.robot"],
            expected_file="autodetect/expected_output.txt",
        )

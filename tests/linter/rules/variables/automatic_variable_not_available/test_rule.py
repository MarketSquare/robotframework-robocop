from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt", issue_format="end_col")

    def test_extended(self):
        self.check_rule(src_files=["extended.robot"], expected_file="expected_extended.txt", output_format="extended")

    def test_exact_identifiers_and_section_shadowing(self):
        self.check_rule(
            src_files=["shadowing.robot"],
            expected_file="expected_shadowing.txt",
            issue_format="end_col",
            test_on_version=">=5",
        )

    def test_source_ordered_assignments_and_setters(self):
        self.check_rule(
            src_files=["assignments.robot"],
            expected_file="expected_assignments.txt",
            issue_format="end_col",
            test_on_version=">=5",
        )

    def test_delayed_teardown_bindings(self):
        self.check_rule(src_files=["teardowns.robot"], expected_file=None, test_on_version=">=5")

    def test_setup_runtime_order(self):
        self.check_rule(
            src_files=["setups.robot"],
            expected_file="expected_setups.txt",
            issue_format="end_col",
            test_on_version=">=5",
        )

    def test_item_assignments_do_not_shadow(self):
        self.check_rule(
            src_files=["item_assignments.robot"],
            expected_file="expected_item_assignments.txt",
            issue_format="end_col",
            test_on_version=">=6.1",
        )

    def test_var_scopes(self):
        self.check_rule(
            src_files=["var_scopes.robot"],
            expected_file="expected_var_scopes.txt",
            issue_format="end_col",
            test_on_version=">=7",
        )

    def test_suites_scope(self):
        self.check_rule(src_files=["suites_scope.robot"], expected_file=None, test_on_version=">=7.1")

    def test_typed_assignments(self):
        self.check_rule(
            src_files=["typed_assignments.robot"],
            expected_file="expected_typed_assignments.txt",
            issue_format="end_col",
            test_on_version=">=7.3",
        )

from tests.linter.utils import RuleAcceptance

SRC_FILES = [
    "bdd_nested_runtime_import_shadow.robot",
    "bdd_runtime_import_shadow.robot",
    "call_method_runtime_import_shadow.robot",
    "test_cases.robot",
    "keywords.robot",
    "default_tags.robot",
    "dynamic_runtime_import_shadow.robot",
    "evaluate_runtime_import_shadow.robot",
    "inline_evaluation_runtime_import_shadow.robot",
    "escaped_runtime_import_shadow.robot",
    "embedded_shadow.robot",
    "late_template_runtime_import_shadow.robot",
    "list_expanded_runtime_import_shadow.robot",
    "localized_bdd_runtime_import_shadow.robot",
    "localized_import.robot",
    "nested_escaped_runtime_import_shadow.robot",
    "nested_runtime_import_shadow.robot",
    "no_tag.robot",
    "qualified_shadow.robot",
    "runtime_import_shadow.robot",
    "shadowed.robot",
    "shadowed_outer.robot",
    "template_runtime_import_shadow.robot",
    "templated.robot",
    "unrelated_run_keyword_shadow.robot",
    "imported_shadow.robot",
]


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=SRC_FILES, expected_file="expected_output.txt", test_on_version=">=5")

    def test_extended(self):
        self.check_rule(
            src_files=["keywords.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
            test_on_version=">=5",
        )

    def test_suite_tags(self):
        self.check_rule(
            src_files=["suite_tags.robot"],
            expected_file="expected_suite_tags.txt",
            test_on_version=">=6",
        )

    def test_fix(self):
        self.check_rule_fix(
            src_files=[
                "bdd_nested_runtime_import_shadow.robot",
                "bdd_runtime_import_shadow.robot",
                "call_method_runtime_import_shadow.robot",
                "test_cases.robot",
                "dynamic_runtime_import_shadow.robot",
                "evaluate_runtime_import_shadow.robot",
                "inline_evaluation_runtime_import_shadow.robot",
                "escaped_runtime_import_shadow.robot",
                "embedded_shadow.robot",
                "late_template_runtime_import_shadow.robot",
                "list_expanded_runtime_import_shadow.robot",
                "localized_bdd_runtime_import_shadow.robot",
                "localized_import.robot",
                "nested_escaped_runtime_import_shadow.robot",
                "nested_runtime_import_shadow.robot",
                "keywords.robot",
                "qualified_shadow.robot",
                "runtime_import_shadow.robot",
                "shadowed.robot",
                "shadowed_outer.robot",
                "template_runtime_import_shadow.robot",
                "templated.robot",
                "unrelated_run_keyword_shadow.robot",
                "imported_shadow.robot",
            ],
            test_on_version=">=5",
        )

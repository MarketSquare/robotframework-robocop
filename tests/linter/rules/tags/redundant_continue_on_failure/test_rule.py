from tests.linter.utils import RuleAcceptance

SRC_FILES = [
    "test_cases.robot",
    "keywords.robot",
    "default_tags.robot",
    "embedded_shadow.robot",
    "localized_import.robot",
    "no_tag.robot",
    "shadowed.robot",
    "shadowed_outer.robot",
    "templated.robot",
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
                "test_cases.robot",
                "embedded_shadow.robot",
                "localized_import.robot",
                "keywords.robot",
                "shadowed.robot",
                "shadowed_outer.robot",
                "templated.robot",
                "imported_shadow.robot",
            ],
            test_on_version=">=5",
        )

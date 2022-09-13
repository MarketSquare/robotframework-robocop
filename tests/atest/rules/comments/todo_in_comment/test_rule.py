from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_added_terms(self):
        self.check_rule(
            config="-c todo-in-comment:markers:todo,fixme,OMG",
            src_files=["added_terms/test.robot"],
            expected_file="added_terms/expected_output.txt",
        )

    def test_phrases(self):
        self.check_rule(
            config=["-c", "todo-in-comment:markers:remove me,fix this ugly bug,korjaa tämä hässäkkä"],
            src_files=["phrases/test.robot"],
            expected_file="phrases/expected_output.txt",
        )

import pytest

from robot.api import get_model

from robocop.utils import AssignmentTypeDetector, parse_assignment_sign_type


def detect_from_file(file):
    model = get_model(file)
    detector = AssignmentTypeDetector()
    detector.visit(model)
    return detector.keyword_most_common, detector.variables_most_common


class TestParseAssignmentSignType:
    @pytest.mark.parametrize('value, expected', [
        ('none', ''),
        ('equal_sign', '='),
        ('space_and_equal_sign', ' =')
    ])
    def test_happy_paths(self, value, expected):
        assert parse_assignment_sign_type(value) == expected

    def test_invalid_value(self):
        with pytest.raises(ValueError) as error:
            parse_assignment_sign_type('=')
        assert "Expected one of ('none', 'equal_sign', 'space_and_equal_sign', 'autodetect') " \
               "but got '=' instead" in str(error)


class TestAssignmentTypeDetector:
    def test_empty_file(self):
        assert detect_from_file('') == (None, None)

    def test_one_assignment(self):
        file = "*** Variables ***\n" \
               "${var}  4\n" \
               "\n" \
               "*** Keywords ***\n" \
               "Keyword\n" \
               "    Other Keyword\n" \
               "    ${var}=  Other Keyword\n"
        assert detect_from_file(file) == (None, None)

    def test_two_var_one_keyword_same_assignments(self):
        file = "*** Variables ***\n" \
               "${var1} =  4\n" \
               "${var2} =  5\n" \
               "\n" \
               "*** Keywords ***\n" \
               "Keyword\n" \
               "    Other Keyword\n" \
               "    ${var}=  Other Keyword\n"
        assert detect_from_file(file) == (None, None)

    def test_two_var_same_two_keyword_diff_assignments(self):
        file = "*** Variables ***\n" \
               "${var1} =  4\n" \
               "${var2} =  5\n" \
               "\n" \
               "*** Keywords ***\n" \
               "Keyword\n" \
               "    Other Keyword\n" \
               "    ${var1}=  Other Keyword\n" \
               "    ${var2}   Other Keyword\n"
        assert detect_from_file(file) == ('=', None)

    def test_five_var_diff_three_keyword_diff_assignments(self):
        file = "*** Variables ***\n" \
               "${var1}=  4\n" \
               "${var2} =  5\n" \
               "${var3}  5\n"\
               "${var4} =  5\n" \
               "${var5} =  5\n" \
               "\n" \
               "*** Keywords ***\n" \
               "Keyword\n" \
               "    Other Keyword\n" \
               "    ${var1}  Other Keyword\n" \
               "    ${var2}=   Other Keyword\n" \
               "    ${var3} =   Other Keyword\n"
        assert detect_from_file(file) == ('', ' =')

import pytest
from robot.api import get_model

from robocop.utils import (
    AssignmentTypeDetector,
    RecommendationFinder,
    find_robot_vars,
    parse_assignment_sign_type,
    pattern_type,
    remove_robot_vars,
)


def detect_from_file(file):
    model = get_model(file)
    detector = AssignmentTypeDetector()
    detector.visit(model)
    return detector.keyword_most_common, detector.variables_most_common


class TestParseAssignmentSignType:
    @pytest.mark.parametrize(
        "value, expected",
        [("none", ""), ("equal_sign", "="), ("space_and_equal_sign", " =")],
    )
    def test_happy_paths(self, value, expected):
        assert parse_assignment_sign_type(value) == expected

    def test_invalid_value(self):
        with pytest.raises(ValueError) as error:
            parse_assignment_sign_type("=")
        assert (
            "Expected one of ('none', 'equal_sign', 'space_and_equal_sign', 'autodetect') "
            "but got '=' instead" in str(error)
        )


class TestAssignmentTypeDetector:
    def test_empty_file(self):
        assert detect_from_file("") == (None, None)

    def test_one_assignment(self):
        file = (
            "*** Variables ***\n"
            "${var}  4\n"
            "\n"
            "*** Keywords ***\n"
            "Keyword\n"
            "    Other Keyword\n"
            "    ${var}=  Other Keyword\n"
        )
        assert detect_from_file(file) == (None, None)

    def test_two_var_one_keyword_same_assignments(self):
        file = (
            "*** Variables ***\n"
            "${var1} =  4\n"
            "${var2} =  5\n"
            "\n"
            "*** Keywords ***\n"
            "Keyword\n"
            "    Other Keyword\n"
            "    ${var}=  Other Keyword\n"
        )
        assert detect_from_file(file) == (None, None)

    def test_two_var_same_two_keyword_diff_assignments(self):
        file = (
            "*** Variables ***\n"
            "${var1} =  4\n"
            "${var2} =  5\n"
            "\n"
            "*** Keywords ***\n"
            "Keyword\n"
            "    Other Keyword\n"
            "    ${var1}=  Other Keyword\n"
            "    ${var2}   Other Keyword\n"
        )
        assert detect_from_file(file) == ("=", None)

    def test_five_var_diff_three_keyword_diff_assignments(self):
        file = (
            "*** Variables ***\n"
            "${var1}=  4\n"
            "${var2} =  5\n"
            "${var3}  5\n"
            "${var4} =  5\n"
            "${var5} =  5\n"
            "\n"
            "*** Keywords ***\n"
            "Keyword\n"
            "    Other Keyword\n"
            "    ${var1}  Other Keyword\n"
            "    ${var2}=   Other Keyword\n"
            "    ${var3} =   Other Keyword\n"
        )
        assert detect_from_file(file) == ("", " =")


class TestRecommendationFinder:
    @pytest.mark.parametrize(
        "name, normalized",
        [
            ("justname", ("justname", "justname")),
            ("just_name", ("just name", "justname")),
            ("just-name", ("just name", "justname")),
            ("name-just", ("just name", "namejust")),
        ],
    )
    def test_normalize(self, name, normalized):
        rec = RecommendationFinder()
        actual = rec.normalize(name)
        assert actual == normalized

    @pytest.mark.parametrize(
        "name, candidates, similar",
        [
            ("", ["some"], ""),
            ("some", [], ""),
            ("is-this", ["this-is", "some"], " Did you mean:\n    this-is"),
            ("is-this1", ["this-is", "some"], " Did you mean:\n    this-is"),
            (
                "is-this",
                ["this-is", "some", "is-this"],
                " Did you mean:\n    is-this\n    this-is",
            ),
            ("is this", ["is-this", "some"], " Did you mean:\n    is-this"),
            (
                "this-is-longernamewithout",
                ["this-is-longer-name-without", "a", "some"],
                " Did you mean:\n    this-is-longer-name-without",
            ),
        ],
    )
    def test_find_similar(self, name, candidates, similar):
        rec = RecommendationFinder().find_similar(name, candidates)
        assert similar == rec


class TestMisc:
    @pytest.mark.parametrize(
        "string, replaced",
        [
            (
                "Keyword With Embedded ${var} Variable",
                "Keyword With Embedded  Variable",
            ),
            (
                "Keyword With Embedded ${var.attr} Variable",
                "Keyword With Embedded  Variable",
            ),
            (
                "Keyword With Embedded ${var}['key'] Variable",
                "Keyword With Embedded  Variable",
            ),
            (
                "Keyword With Embedded ${var}[${var}] Variable",
                "Keyword With Embedded  Variable",
            ),
            ("${variable}", ""),
            ("a${variable}", "a"),
            ("%{variable}b", "b"),
            ("a@{variable}b", "ab"),
            ("${variable${nested}suffix}", ""),
            ('&{dict["key"]}', ""),
            ("this is ${variable not closed properly", "this is "),
            (r"this is \${ escaped", r"this is \${ escaped"),
        ],
    )
    def test_remove_robot_vars(self, string, replaced):
        actual = remove_robot_vars(string)
        assert actual == replaced

    @pytest.mark.parametrize(
        "string, exp_vars",
        [
            ("${var}", [(0, 6)]),
            ("${var}}", [(0, 6)]),
            (r"\$${var}}", [(2, 8)]),
            (
                "This is some ${var} and another ${var} but also ${${nested}}",
                [(13, 19), (32, 38), (48, 60)],
            ),
        ],
    )
    def test_find_robot_vars(self, string, exp_vars):
        assert find_robot_vars(string) == exp_vars

    def test_invalid_pattern_type(self):
        with pytest.raises(ValueError) as error:
            pattern_type(r"[\911]")
        assert r"Invalid regex pattern: bad escape \\9 at position 1" in str(error)

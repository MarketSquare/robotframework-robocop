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
from robocop.utils.version_matching import Version, VersionSpecifier


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
            ("is-this", ["this-is", "some"], "Did you mean:\n    this-is"),
            ("is-this1", ["this-is", "some"], "Did you mean:\n    this-is"),
            (
                "is-this",
                ["this-is", "some", "is-this"],
                "Did you mean:\n    is-this\n    this-is",
            ),
            ("is this", ["is-this", "some"], "Did you mean:\n    is-this"),
            (
                "this-is-longernamewithout",
                ["this-is-longer-name-without", "a", "some"],
                "Did you mean:\n    this-is-longer-name-without",
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


@pytest.mark.parametrize(
    "robot_version, rule_version, should_pass",
    [
        ("6.0.2", ">=6", True),
        ("6.1a2.dev1", ">=6", True),
        ("6.0rc2.dev1", ">=6", False),
        ("6.0pre2.dev1", ">=6", False),
        ("6.0.2", "<5", False),
        ("6.1a2.dev1", "<=5", False),
        ("6.1a2.dev1", "~=5.0", False),
        ("6.0rc2.dev1", "<=6", True),
        ("6.0rc2.dev", "<=6", True),
        ("5.0", "<=5dev1", False),
        ("5.0", ">5dev1", False),
        ("5.0", ">5.0.dev1", False),
        ("6.0dev0", ">=6", False),
        ("6.0", ">=6", True),
        ("6", ">=6", True),
        ("5.0.2", ">=6", False),
        ("5.1b2.dev1", ">=6", False),
        ("5.1alpha2.dev1", ">=6", False),
        ("5.1beta2.dev1", "<6", True),
        ("5.1beta2.dev1", "!=6", True),
        ("6.0.2", "<4.0", False),
        ("3.2.1", "<4.0", True),
        ("5.0", "==5", True),
        ("5.1", "==5", False),
        ("4.0", "==4.*", True),
        ("4.0", "~=4.0", True),
        ("4.0", "~=5.0", False),
        ("4.0", "!=4", False),
        ("4.0", "!=5", True),
    ],
)
def test_version_specifier(robot_version, rule_version, should_pass):
    rf_version = Version(robot_version)
    rule_version_spec = VersionSpecifier(rule_version)
    assert (str(rf_version) in rule_version_spec) == should_pass


def test_version_parsing_and_comparison():
    versions = [Version("4"), Version("4.0"), Version("4.0.0"), Version("4.0.0dev1")]
    equal_version = Version("4")
    higher_version = Version("5")
    lower_version = Version("3")
    for version in versions:
        assert (version.major, version.minor, version.micro) == (4, 0, 0)
        if version.dev is None:
            assert version == equal_version
            assert version >= equal_version
        else:
            assert version != equal_version
            assert not version >= equal_version
        assert version <= equal_version
        assert version < higher_version
        assert not version > higher_version
        assert version > lower_version
        assert not version < lower_version


def test_invalid_version_specifier():
    with pytest.raises(ValueError, match="Invalid specifier: '=<5'"):
        VersionSpecifier("=<5")

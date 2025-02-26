import pytest

from robocop.linter.utils.version_matching import Version, VersionSpecifier


@pytest.mark.parametrize(
    ("robot_version", "rule_version", "should_pass"),
    [
        ("6.0.2", ">=6", True),
        ("6.1a2.dev1", ">=6", True),
        ("6.0rc2.dev1", ">=6", True),
        ("6.0pre2.dev1", ">=6", True),
        ("6.0.2", "<5", False),
        ("6.1a2.dev1", "<=5", False),
        ("6.1a2.dev1", "~=5.0", False),
        ("6.0rc2.dev1", "<=6", True),
        ("6.0rc2.dev", "<=6", True),
        ("6.0dev0", ">=6", True),
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
        assert version == equal_version
        assert version >= equal_version
        assert version <= equal_version
        assert version < higher_version
        assert not version > higher_version
        assert version > lower_version
        assert not version < lower_version


def test_invalid_version_specifier():
    with pytest.raises(ValueError, match="Invalid specifier: '=<5'"):
        VersionSpecifier("=<5")

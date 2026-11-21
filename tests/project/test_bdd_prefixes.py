"""Tests for recognizing localized and multi-word BDD prefixes."""

from __future__ import annotations

import pytest
from robot.api import Token, get_model

from robocop.parsing.run_keywords import (
    BDD_PREFIXES,
    bdd_prefixes_for,
    get_bdd_prefix,
    is_bdd_prefix,
    iterate_keyword_calls,
    remove_bdd_prefix,
)
from robocop.run import check_files
from robocop.version_handling import ROBOT_VERSION, Version

try:
    from robot.api import Languages
except ImportError:  # RF < 6.0
    Languages = None

requires_languages = pytest.mark.skipif(
    ROBOT_VERSION < Version("6.0"),  # noqa: SIM300
    reason="Languages were added in RF 6.0",
)

FRENCH = frozenset({"Soit", "Étant Donné", "Étant Donné Que", "Et", "Et Que", "Mais", "Quand", "Alors"})


class TestGetBddPrefix:
    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("Given Login", "Given"),
            ("given Login", "given"),
            ("GIVEN Login", "GIVEN"),
            ("And Login", "And"),
            ("Login", None),
            ("Given", None),
            ("Givenx Login", None),
            ("Logged In Given", None),
        ],
    )
    def test_english(self, name, expected):
        assert get_bdd_prefix(name) == expected

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("Soit User Is Ready", "Soit"),
            ("Étant donné que User Is Ready", "Étant donné que"),
            ("Étant donné User Is Ready", "Étant donné"),
            ("Et que User Is Ready", "Et que"),
            ("Et User Is Ready", "Et"),
            ("Etc Something", None),
        ],
    )
    def test_longest_prefix_wins(self, name, expected):
        assert get_bdd_prefix(name, FRENCH) == expected

    def test_any_whitespace_between_prefix_words(self):
        assert get_bdd_prefix("Et\u00a0que User Is Ready", FRENCH) == "Et\u00a0que"
        assert get_bdd_prefix("Et\tque User Is Ready", FRENCH) == "Et\tque"

    @requires_languages
    @pytest.mark.parametrize("prefix", ["Diyelim ki", "diyelim ki", "DİYELİM Kİ", "DIYELIM KI"])
    def test_unicode_case_variants(self, prefix):
        """Robot Framework matches prefixes with ``re.IGNORECASE``, ``str.lower`` changes the length of ``İ``."""
        turkish = bdd_prefixes_for(Languages(["tr"]))
        if not turkish & {"Diyelim Ki"}:
            pytest.skip("Turkish 'Diyelim ki' prefix is not available in this Robot Framework version")
        assert get_bdd_prefix(f"{prefix} User Is Ready", turkish) == prefix
        assert is_bdd_prefix(prefix, turkish)

    @pytest.mark.parametrize(
        ("name", "expected"),
        [("Given", True), ("GIVEN", True), ("Et  que", True), ("Et\u00a0que", True), ("Et que x", False), ("", False)],
    )
    def test_is_bdd_prefix(self, name, expected):
        assert is_bdd_prefix(name, FRENCH | BDD_PREFIXES) is expected

    def test_remove_multi_word_prefix(self):
        assert remove_bdd_prefix("Et que User Is Ready", FRENCH) == "User Is Ready"
        assert remove_bdd_prefix("Étant donné que User Is Ready", FRENCH) == "User Is Ready"

    def test_remove_without_prefix_returns_name(self):
        assert remove_bdd_prefix("User Is Ready", FRENCH) == "User Is Ready"


class TestBddPrefixesFor:
    def test_no_languages_gives_english(self):
        assert bdd_prefixes_for(None) == BDD_PREFIXES

    @requires_languages
    def test_languages_include_english_and_configured(self):
        prefixes = bdd_prefixes_for(Languages(["fr"]))
        assert "Given" in prefixes
        assert "Étant Donné" in prefixes


@requires_languages
def test_run_keyword_with_localized_prefix_is_resolved():
    model = get_model("*** Test Cases ***\nTest\n    Angenommen Run Keyword    Nested Keyword\n")
    node = model.sections[0].body[0].body[0]
    prefixes = bdd_prefixes_for(Languages(["de"]))
    names = [call.name.value for call in iterate_keyword_calls(node, Token.KEYWORD, prefixes)]
    assert names == ["Angenommen Run Keyword", "Nested Keyword"]


GERMAN = """\
Language: de

*** Testfälle ***
Login
    Angenommen User Is Logged In
    Wenn User Opens Settings


*** Schlüsselwörter ***
User Is Logged In
    No Operation

User Opens Settings
    No Operation
"""

FRENCH_SUITE = """\
Language: fr

*** Unités de test ***
Login
    Étant donné User Is Ready
    Et User Is Ready


*** Mots-clés ***
User Is Ready
    No Operation
"""

FRENCH_SUITE_WITH_QUE = """\
Language: fr

*** Unités de test ***
Login
    Étant donné que User Is Ready
    Et que User Is Ready


*** Mots-clés ***
User Is Ready
    No Operation
"""

GERMAN_WITHOUT_HEADER = """\
*** Test Cases ***
Login
    Angenommen User Is Logged In


*** Keywords ***
User Is Logged In
    No Operation
"""


def run(source, select, **kwargs):
    return check_files(
        sources=[source],
        select=select,
        root=source,
        ignore_file_config=True,
        return_result=True,
        cache=False,
        silent=True,
        **kwargs,
    )


def reported(diagnostics):
    return sorted(f"{diag.source.path.name}:{diag.range.start.line} {diag.rule.name}" for diag in diagnostics)


@requires_languages
class TestProjectRulesWithLocalizedPrefixes:
    def test_language_header(self, tmp_path):
        (tmp_path / "de.robot").write_text(GERMAN, encoding="utf-8")
        (tmp_path / "fr.robot").write_text(FRENCH_SUITE, encoding="utf-8")
        assert reported(run(tmp_path, ["keyword-not-found", "unused-keyword"])) == []

    def test_prefix_extending_shorter_prefix(self, tmp_path):
        """``Et que`` must not be cut after ``Et``, which would leave the wrong name ``que User Is Ready``."""
        if "Et Que" not in bdd_prefixes_for(Languages(["fr"])):
            pytest.skip("French 'que' prefixes are not available in this Robot Framework version")
        (tmp_path / "fr.robot").write_text(FRENCH_SUITE_WITH_QUE, encoding="utf-8")
        assert reported(run(tmp_path, ["keyword-not-found", "unused-keyword"])) == []

    def test_language_option(self, tmp_path):
        (tmp_path / "de.robot").write_text(GERMAN_WITHOUT_HEADER, encoding="utf-8")
        assert reported(run(tmp_path, ["keyword-not-found", "unused-keyword"], language=["de"])) == []

    def test_language_of_one_file_does_not_leak(self, tmp_path):
        (tmp_path / "a_de.robot").write_text(GERMAN, encoding="utf-8")
        (tmp_path / "b_en.robot").write_text(GERMAN_WITHOUT_HEADER, encoding="utf-8")
        assert reported(run(tmp_path, ["keyword-not-found"])) == ["b_en.robot:3 keyword-not-found"]


@requires_languages
def test_bdd_without_keyword_call_localized(tmp_path):
    (tmp_path / "de.robot").write_text(
        "Language: de\n\n*** Testfälle ***\nLogin\n    Angenommen\n    Wenn    Something\n", encoding="utf-8"
    )
    assert reported(run(tmp_path, ["bdd-without-keyword-call"], project=False)) == [
        "de.robot:5 bdd-without-keyword-call",
        "de.robot:6 bdd-without-keyword-call",
    ]


@requires_languages
def test_bdd_without_keyword_call_unicode_case(tmp_path):
    if "Diyelim Ki" not in bdd_prefixes_for(Languages(["tr"])):
        pytest.skip("Turkish 'Diyelim ki' prefix is not available in this Robot Framework version")
    (tmp_path / "tr.robot").write_text(
        "Language: tr\n\n*** Test Cases ***\nLogin\n    D\u0130YEL\u0130M K\u0130\n", encoding="utf-8"
    )
    assert reported(run(tmp_path, ["bdd-without-keyword-call"], project=False)) == [
        "tr.robot:5 bdd-without-keyword-call"
    ]


@requires_languages
def test_project_rules_with_unicode_prefix_variants(tmp_path):
    if "Et Que" not in bdd_prefixes_for(Languages(["fr"])):
        pytest.skip("French 'que' prefixes are not available in this Robot Framework version")
    (tmp_path / "fr.robot").write_text(
        "Language: fr\n\n*** Unités de test ***\nLogin\n    Et\u00a0que User Is Ready\n\n"
        "*** Mots-cl\u00e9s ***\nUser Is Ready\n    No Operation\n",
        encoding="utf-8",
    )
    assert reported(run(tmp_path, ["keyword-not-found", "unused-keyword"])) == []


@requires_languages
def test_continue_on_failure_call_with_localized_prefix(tmp_path):
    (tmp_path / "de.robot").write_text(
        "Language: de\n\n*** Testfälle ***\nLogin\n"
        "    [Tags]    robot:continue-on-failure\n"
        "    Angenommen Run Keyword And Continue On Failure    Log    message\n",
        encoding="utf-8",
    )
    assert reported(run(tmp_path, ["unnecessary-continue-on-failure"], project=False)) == [
        "de.robot:6 unnecessary-continue-on-failure"
    ]


@requires_languages
def test_nested_run_keyword_with_localized_prefix_is_checked(tmp_path):
    (tmp_path / "de.robot").write_text(
        "Language: de\n\n*** Testfälle ***\nLogin\n    Angenommen Run Keyword    Sleep    1s\n", encoding="utf-8"
    )
    diagnostics = run(
        tmp_path, ["not-allowed-keyword"], project=False, configure=["not-allowed-keyword.keywords=sleep"]
    )
    assert reported(diagnostics) == ["de.robot:5 not-allowed-keyword"]


@requires_languages
def test_language_from_directory_config_invalidates_cache(tmp_path):
    project = tmp_path / "project"
    (project / "de").mkdir(parents=True)
    (project / "robocop.toml").write_text("")
    (project / "de" / "test.robot").write_text(GERMAN_WITHOUT_HEADER, encoding="utf-8")

    def run_cached():
        return check_files(
            sources=[project],
            select=["keyword-not-found"],
            root=project,
            return_result=True,
            cache=True,
            cache_dir=tmp_path / "cache",
            silent=True,
        )

    assert reported(run_cached()) == ["test.robot:3 keyword-not-found"]
    (project / "de" / "robocop.toml").write_text('language = ["de"]\n')
    assert reported(run_cached()) == []

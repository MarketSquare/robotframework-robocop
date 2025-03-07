from __future__ import annotations

from robot.api import Token
from robot.api.parsing import CommentSection, EmptyLine

try:
    from robot.api import Language
    from robot.api.parsing import Config
except ImportError:  # RF 6.0
    Config, Language = None, None
try:
    from robot.parsing.model.blocks import ImplicitCommentSection
except ImportError:  # RF < 6.1
    ImplicitCommentSection = None

from robocop.formatter.disablers import skip_if_disabled, skip_section_if_disabled
from robocop.formatter.exceptions import InvalidParameterValueError
from robocop.formatter.formatters import Formatter


class Translate(Formatter):
    """
    Translate Robot Framework source files from one or many languages to different one.

    Following code:

    ```robotframework
    *** Test Cases ***
    Test case
        [Setup]    Keyword
        Step
    ```

    will be formatted to (with the German language configured):

    ```robotframework
    *** Testfälle ***
    Test case
        [Vorbereitung]    Keyword
        Step
    ```

    You can configure destination language with ``language`` parameter (default ``en``). If your file is not written
    in english you also need to configure source language - either using cli option or language header in the
    source files:

    ```
    robocop format -c Translate.enabled=True -c Translate.language=uk --language pl,de source_in_pl_and_de.robot
    ```

    BDD keywords are not translated by default. Set ``translate_bdd`` parameter to ``True`` to enable it.
    If there is more than one alternative to BDD keyword the first one (sorted alphabetically) will be chosen.
    It can be overwritten using ``<bdd_keyword>_alternative`` parameters.
    """

    ENABLED = False
    MIN_VERSION = 6

    def __init__(
        self,
        language: str = "en",
        translate_bdd: bool = False,
        add_language_header: bool = False,
        but_alternative: str | None = None,
        given_alternative: str | None = None,
        and_alternative: str | None = None,
        then_alternative: str | None = None,
        when_alternative: str | None = None,
    ):
        super().__init__()
        self.in_settings = False
        self.translate_bdd = translate_bdd
        self.add_language_header = add_language_header
        if Language is not None:
            self.language = Language.from_name(language)
            # reverse mapping, in core it's other_lang: en and we need en: other_lang name
            self.settings = {value: key.title() for key, value in self.language.settings.items() if key}
        else:
            self.language, self.settings = None, None
        self._bdd_mapping = None
        self.bdd = self.get_translated_bdd(
            but_alternative, given_alternative, and_alternative, then_alternative, when_alternative
        )

    @property
    def bdd_mapping(self):
        if self._bdd_mapping is None:
            self._bdd_mapping = {}
            for language in self.languages:
                self._bdd_mapping.update({name.title(): "But" for name in language.but_prefixes})
                self._bdd_mapping.update({name.title(): "Given" for name in language.given_prefixes})
                self._bdd_mapping.update({name.title(): "And" for name in language.and_prefixes})
                self._bdd_mapping.update({name.title(): "Then" for name in language.then_prefixes})
                self._bdd_mapping.update({name.title(): "When" for name in language.when_prefixes})
        return self._bdd_mapping

    def get_bdd_keyword(self, container: set, alternative: str | None, param_name: str) -> str:
        if alternative is not None:
            names = ",".join(sorted(container))
            if alternative not in container:
                raise InvalidParameterValueError(
                    self.__class__.__name__,
                    param_name,
                    alternative,
                    f"Provided BDD keyword alternative does not exist in the destination language. "
                    f"Select one of: {names}",
                )
            return alternative.title()
        return sorted(kw.title() for kw in container)[0]

    def get_translated_bdd(
        self,
        but_alternative: str | None,
        given_alternative: str | None,
        and_alternative: str | None,
        then_alternative: str | None,
        when_alternative: str | None,
    ):
        if not self.translate_bdd:
            return {}
        return {
            "But": self.get_bdd_keyword(self.language.but_prefixes, but_alternative, "but_alternative"),
            "Given": self.get_bdd_keyword(self.language.given_prefixes, given_alternative, "given_alternative"),
            "And": self.get_bdd_keyword(self.language.and_prefixes, and_alternative, "and_alternative"),
            "Then": self.get_bdd_keyword(self.language.then_prefixes, then_alternative, "then_alternative"),
            "When": self.get_bdd_keyword(self.language.when_prefixes, when_alternative, "when_alternative"),
        }

    def add_replace_language_header(self, node):
        """
        Add or replaces language headers in formatted files.

        If the file already contains language header it will be replaced.
        If the destination language is English, it will be removed.
        """
        if not self.add_language_header or not node.sections:
            return node
        if isinstance(node.sections[0], CommentSection) and node.sections[0].header is None:
            if node.sections[0].body and isinstance(node.sections[0].body[0], Config):
                if self.language.code == "en":
                    node.sections[0].body.pop(0)
                else:
                    node.sections[0].body[0] = Config.from_params(f"language: {self.language.code}")
            else:
                node.sections[0].body.insert(0, Config.from_params(f"language: {self.language.code}"))
        elif self.language.code != "en":
            language_header = Config.from_params(f"language: {self.language.code}")
            empty_line = EmptyLine.from_params()
            if ImplicitCommentSection:
                section = ImplicitCommentSection(body=[language_header, empty_line])
            else:
                section = CommentSection(header=None, body=[language_header, empty_line])
            node.sections.insert(0, section)
        return node

    def visit_File(self, node):  # noqa: N802
        self.in_settings = False
        self.add_replace_language_header(node)
        return self.generic_visit(node)

    @skip_if_disabled
    def visit_KeywordCall(self, node):  # noqa: N802
        """
        Translate BDD keyword in Keyword Call.

        BDD is translated only if keyword call name starts with BDD, it is recognized as BDD and there is one space of
        separation before rest of the keyword name.
        Example of keyword name with BDD keyword:
            Given I Open Main Page
        Source keyword call can be written in any language - that's why we need to translate first word of the keyword
        to English then to destination language.
        """
        if not self.translate_bdd or not node.keyword:
            return node
        prefix, *name = node.keyword.split(maxsplit=1)
        if not name or prefix.title() not in self.languages.bdd_prefixes:
            return node
        english_bdd = self.bdd_mapping.get(prefix.title(), None)
        if not english_bdd:
            return node
        translated_bdd = self.bdd[english_bdd]
        name_token = node.get_token(Token.KEYWORD)
        name_token.value = f"{translated_bdd} {name[0]}"
        return node

    @skip_section_if_disabled
    def translate_section_header(self, node, eng_name):
        translated_value = getattr(self.language, eng_name)
        translated_value = translated_value.title()
        name_token = node.header.data_tokens[0]
        name_token.value = f"*** {translated_value} ***"
        return self.generic_visit(node)

    def visit_SettingSection(self, node):  # noqa: N802
        self.in_settings = True
        node = self.translate_section_header(node, "settings_header")
        self.in_settings = False
        return node

    def visit_TestCaseSection(self, node):  # noqa: N802
        return self.translate_section_header(node, "test_cases_header")

    def visit_KeywordSection(self, node):  # noqa: N802
        return self.translate_section_header(node, "keywords_header")

    def visit_VariableSection(self, node):  # noqa: N802
        return self.translate_section_header(node, "variables_header")

    def visit_CommentSection(self, node):  # noqa: N802
        if node.header is None:
            return node
        return self.translate_section_header(node, "comments_header")

    @skip_if_disabled
    def visit_ForceTags(self, node):  # noqa: N802
        node_type = node.data_tokens[0].value.title()
        # special handling because it's renamed in 6.0
        if node_type == "Force Tags":
            node_type = "Test Tags"  # TODO: Handle Task/Test types
        english_value = self.languages.settings.get(node_type, None)
        if english_value is None:
            return node
        translated_value = self.settings.get(english_value, None)
        if translated_value is None:
            return node
        node.data_tokens[0].value = translated_value.title()
        return node

    visit_TestTags = visit_TaskTags = visit_ForceTags  # noqa: N815

    @skip_if_disabled
    def visit_Setup(self, node):  # noqa: N802
        node_type = node.type.title()
        translated_value = self.settings.get(node_type, None)
        if translated_value is None:
            return node
        if not self.in_settings:
            translated_value = f"[{translated_value}]"
        node.data_tokens[0].value = translated_value
        return self.generic_visit(node)

    visit_Teardown = visit_Template = visit_Timeout = visit_Arguments = visit_Tags = visit_Documentation = (  # noqa: N815
        visit_Metadata  # noqa: N815
    ) = visit_SuiteSetup = visit_SuiteTeardown = visit_TestSetup = visit_TestTeardown = visit_TestTemplate = (  # noqa: N815
        visit_TestTimeout  # noqa: N815
    ) = visit_KeywordTags = visit_LibraryImport = visit_VariablesImport = visit_ResourceImport = visit_Setup  # noqa: N815

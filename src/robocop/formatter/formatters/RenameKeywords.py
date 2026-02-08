from __future__ import annotations

import re
from typing import TYPE_CHECKING

from robot.api.parsing import Token

from robocop.exceptions import InvalidParameterValueError
from robocop.formatter.disablers import skip_if_disabled, skip_section_if_disabled
from robocop.formatter.formatters import Formatter
from robocop.formatter.utils import misc
from robocop.parsing.run_keywords import RUN_KEYWORDS
from robocop.parsing.string_operations import StringPart, map_string_to_mask

if TYPE_CHECKING:
    from re import Pattern

    from robot.parsing.model.blocks import Section
    from robot.parsing.model.statements import KeywordCall, KeywordName, Setup, SuiteSetup


def validate_choice(formatter: Formatter, choices: list[str], param_name: str, value: str) -> str:
    if value not in choices:
        raise InvalidParameterValueError(
            formatter.__class__.__name__,
            param_name,
            value,
            f"Supported values: {', '.join(choices)}",
        )
    return value


class RenameKeywords(Formatter):
    r"""
    Enforce keyword naming.

    Title Case is applied to keyword name and underscores are replaced by spaces.

    To ignore keywords case set ``keyword_case`` to ``ignore``.
    To keep underscores, set ``remove_underscores`` to ``False``:

    ```
    robocop format --select RenameKeywords -c RenameKeywords.remove_underscores=False .
    ```

    It is also possible to configure `replace_pattern` parameter to find and replace regex pattern. Use `replace_to`
    to set replacement value. This configuration (underscores are used instead of spaces):

    ```
    robocop format --select RenameKeywords -c RenameKeywords.replace_pattern=^(?i)rename\s?me$
    -c RenameKeywords.replace_to=New_Shining_Name .
    ```

    will format following code:

    ```robotframework
    *** Keywords ***
    rename Me
       Keyword Call
    ```

    To:

    ```robotframework
    *** Keywords ***
    New Shining Name
        Keyword Call
    ```

    Use `ignore_library = True` parameter to control if the library name part (Library.Keyword) of keyword call
    should be renamed.
    """

    ENABLED = False

    def __init__(
        self,
        replace_pattern: str | None = None,
        replace_to: str | None = None,
        remove_underscores: bool = True,
        ignore_library: bool = True,
        keyword_case: str = "capitalize_words",
        case_normalization: str = "first_letter",
    ) -> None:
        super().__init__()
        self.ignore_library: bool = ignore_library
        self.remove_underscores: bool = remove_underscores
        self.keyword_case: str = validate_choice(
            self, ["capitalize_words", "capitalize_first", "ignore"], "keyword_case", keyword_case
        )
        self.case_normalization: str = validate_choice(
            self, ["first_letter", "full"], "case_normalization", case_normalization
        )
        self.replace_pattern: Pattern[str] | None = self.parse_pattern(replace_pattern)
        self.replace_to: str = "" if replace_to is None else replace_to

    def parse_pattern(self, replace_pattern: str | None) -> Pattern[str] | None:
        if replace_pattern is None:
            return None
        try:
            return re.compile(replace_pattern)
        except re.error as err:
            raise InvalidParameterValueError(
                self.__class__.__name__,
                "replace_pattern",
                replace_pattern,
                f"It should be a valid regex expression. Regex error: '{err.msg}'",
            ) from None

    @skip_section_if_disabled
    def visit_Section(self, node: Section) -> Section:  # noqa: N802
        return self.generic_visit(node)

    def rename_node(self, token: Token, is_keyword_call: bool) -> None:
        if self.skip.keyword_call_name(token.value):
            return
        new_value = self.normalize_name(token.value, is_keyword_call=is_keyword_call)
        if self.replace_pattern is not None:
            normalized_replace = self.normalize_name(self.replace_to, is_keyword_call=False)
            new_value = self.replace_pattern.sub(repl=normalized_replace, string=new_value)
        new_value = new_value.strip()
        if not new_value:  # do not allow renaming that removes keywords altogether
            return
        token.value = new_value

    def normalize_name(self, value: str, is_keyword_call: bool) -> str:
        result = []
        for i, (part, part_type) in enumerate(map_string_to_mask(value)):
            string_start = i == 0
            if part_type == StringPart.MASKED:
                result.append(part)
            elif string_start and is_keyword_call and self.ignore_library:
                lib_name, *kw_name = part.rsplit(".", maxsplit=1)
                if kw_name:
                    result.append(f"{lib_name}.{self.remove_underscores_and_capitalize(kw_name[0], string_start)}")
                else:
                    result.append(self.remove_underscores_and_capitalize(part, string_start))
            else:
                result.append(
                    ".".join(
                        [
                            self.remove_underscores_and_capitalize(name_part, string_start)
                            for name_part in part.split(".")
                        ]
                    )
                )
        return "".join(result)

    def remove_underscores_and_capitalize(self, value: str, string_start: bool = True) -> str:
        if self.remove_underscores:
            value = value.replace("_", " ")
            value = re.sub(r" +", " ", value)  # replace one or more spaces by one
        if self.keyword_case == "ignore":
            return value
        if self.keyword_case == "capitalize_first":
            if not string_start:
                return self.normalize_case_of_word(value)
            return value[0].upper() + self.normalize_case_of_word(value[1:]) if value else value
        words = []
        split_words = value.split(" ")
        for index, word in enumerate(split_words):
            if not word:
                if index in (0, len(split_words) - 1):  # leading and trailing whitespace
                    words.append("")
            else:
                words.append(word[0].upper() + self.normalize_case_of_word(word[1:]))
        return " ".join(words)

    def normalize_case_of_word(self, word: str) -> str:
        if self.case_normalization == "first_letter":  # better mode switch, maybe boolean flag
            return word
        return word.lower()

    @skip_if_disabled
    def visit_KeywordName(self, node: KeywordName) -> KeywordName:  # noqa: N802
        name_token = node.get_token(Token.KEYWORD_NAME)
        if not name_token or not name_token.value:
            return node
        self.rename_node(name_token, is_keyword_call=False)
        return node

    @skip_if_disabled
    def visit_KeywordCall(self, node: KeywordCall) -> KeywordCall:  # noqa: N802
        name_token = node.get_token(Token.KEYWORD)
        if not name_token or not name_token.value:
            return node
        # ignore assign, separators and comments
        _, tokens = misc.split_on_token_type(node.data_tokens, Token.KEYWORD)
        self.parse_run_keyword(tokens)
        return node

    def parse_run_keyword(self, tokens: list[Token]) -> None:
        if not tokens:
            return None
        self.rename_node(tokens[0], is_keyword_call=True)
        run_keyword = RUN_KEYWORDS.get(tokens[0].value)
        if not run_keyword:
            return None
        tokens = tokens[run_keyword.resolve :]
        if run_keyword.branches:
            if "ELSE IF" in run_keyword.branches:
                while misc.is_token_value_in_tokens("ELSE IF", tokens):
                    prefix, _branch, tokens = misc.split_on_token_value(tokens, "ELSE IF", 2)
                    self.parse_run_keyword(prefix)
            if "ELSE" in run_keyword.branches and misc.is_token_value_in_tokens("ELSE", tokens):
                prefix, _branch, tokens = misc.split_on_token_value(tokens, "ELSE", 1)
                self.parse_run_keyword(prefix)
                self.parse_run_keyword(tokens)
                return None
        elif run_keyword.split_on_and:
            return self.split_on_and(tokens)
        self.parse_run_keyword(tokens)
        return None

    def split_on_and(self, tokens: list[Token]) -> None:
        if not misc.is_token_value_in_tokens("AND", tokens):
            for token in tokens:
                self.rename_node(token, is_keyword_call=True)
            return
        while misc.is_token_value_in_tokens("AND", tokens):
            prefix, _branch, tokens = misc.split_on_token_value(tokens, "AND", 1)
            self.parse_run_keyword(prefix)
        self.parse_run_keyword(tokens)

    @skip_if_disabled
    def visit_SuiteSetup(self, node: SuiteSetup) -> SuiteSetup:  # noqa: N802
        if node.errors:
            return node
        self.parse_run_keyword(node.data_tokens[1:])
        return node

    visit_SuiteTeardown = visit_TestSetup = visit_TestTeardown = visit_SuiteSetup  # noqa: N815

    @skip_if_disabled
    def visit_Setup(self, node: Setup) -> Setup:  # noqa: N802
        if node.errors:
            return node
        self.parse_run_keyword(node.data_tokens[1:])
        return node

    visit_Teardown = visit_Setup  # noqa: N815

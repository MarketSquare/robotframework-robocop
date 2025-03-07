from __future__ import annotations

import re

from robot.api.parsing import Token

from robocop.formatter.disablers import skip_if_disabled, skip_section_if_disabled
from robocop.formatter.exceptions import InvalidParameterValueError
from robocop.formatter.formatters import Formatter

IGNORE_CHARS = {"(", "[", "{", "!", "?"}


def cap_string_until_succeed(word: str):
    """Yield characters from the word and capitalize character until we are able to make char uppercase."""
    capitalize = True
    for char in word:
        if capitalize:
            # chars like numbers, -, dots, commas etc. will not change case, and we should not capitalize further
            if char == char.upper() and char not in IGNORE_CHARS:
                capitalize = False
            else:
                char = char.upper()
                capitalize = not char.isupper()
        yield char


def cap_word(word: str):
    """
    Capitalize the word. The word can start with ( or contain ':

        word -> Word
        (word -> (Word
        word's -> Word's

    """
    if not word or any(c.isupper() for c in word):  # ignore JIRA or sOme
        return word
    new_word = word.capitalize()
    if new_word != word:
        return new_word
    return "".join(cap_string_until_succeed(word))


class RenameTestCases(Formatter):
    r"""
    Enforce test case naming.

    Capitalize first letter of test case name, remove trailing dot and strip leading/trailing whitespace. If
    capitalize_each_word is true, will capitalize each word in test case name.

    It is also possible to configure `replace_pattern` parameter to find and replace regex pattern. Use `replace_to`
    to set replacement value. This configuration:

    ```
    robocop format --formatter RenameTestCases -c RenameTestCases.replace_pattern=[A-Z]{3,}-\d{2,}
    -c RenameTestCases.replace_to=foo
    ```

    will format following code:

    ```robotframework
    *** Test Cases ***
    test ABC-123
        No Operation
    ```

    To:

    ```robotframework
    *** Test Cases ***
    Test foo
        No Operation
    ```

    ```
    robocop format --select RenameTestCases -c RenameTestCases.capitalize_each_word=True
    ```

    will format following code:

    ```robotframework
    *** Test Cases ***
    compare XML with json
        No Operation
    ```

    To:

    ```robotframework
    *** Test Cases ***
    Compare XML With Json
        No Operation
    ```
    """

    ENABLED = False

    def __init__(
        self,
        replace_pattern: str | None = None,
        replace_to: str | None = None,
        capitalize_each_word: bool = False,
    ):
        super().__init__()
        try:
            self.replace_pattern = re.compile(replace_pattern) if replace_pattern is not None else None
        except re.error as err:
            raise InvalidParameterValueError(
                self.__class__.__name__,
                "replace_pattern",
                replace_pattern,
                f"It should be a valid regex expression. Regex error: '{err.msg}'",
            ) from None
        self.replace_to = "" if replace_to is None else replace_to
        self.capitalize_each_word = capitalize_each_word

    @skip_section_if_disabled
    def visit_TestCaseSection(self, node):  # noqa: N802
        return self.generic_visit(node)

    @skip_if_disabled
    def visit_TestCaseName(self, node):  # noqa: N802
        token = node.get_token(Token.TESTCASE_NAME)
        if token.value:
            if self.capitalize_each_word:
                value = token.value.strip()
                token.value = " ".join(cap_word(word) for word in value.split(" "))
            else:
                token.value = token.value[0].upper() + token.value[1:]
            if self.replace_pattern is not None:
                token.value = self.replace_pattern.sub(repl=self.replace_to, string=token.value)
            token.value = token.value.removesuffix(".")
            token.value = token.value.strip()
        return node

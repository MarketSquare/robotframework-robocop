import string

from robotidy.disablers import skip_section_if_disabled
from robotidy.skip import Skip
from robotidy.transformers import Transformer


class NormalizeSectionHeaderName(Transformer):
    """
    Normalize section headers names.
    Robot Framework is quite flexible with the section header naming. Following lines are equal:

    ```robotframework
    *setting
    *** SETTINGS
    *** SettingS ***
    ```

    This transformer normalizes naming to follow ``*** SectionName ***`` format (with plural variant):

    ```robotframework
    *** Settings ***
    *** Keywords ***
    *** Test Cases ***
    *** Variables ***
    *** Comments ***
    ```

    Optional data after section header (for example data driven column names) is preserved.
    It is possible to upper case section header names by passing ``uppercase=True`` parameter:

    ```robotframework
    *** SETTINGS ***
    ```
    """

    HANDLES_SKIP = frozenset({"skip_sections"})
    EN_SINGULAR_HEADERS = {"comment", "setting", "variable", "task", "test case", "keyword"}

    def __init__(self, uppercase: bool = False, skip: Skip = None):
        super().__init__(skip)
        self.uppercase = uppercase

    @skip_section_if_disabled
    def visit_Section(self, node):  # noqa
        return self.generic_visit(node)

    def visit_SectionHeader(self, node):  # noqa
        if not node.name:
            return node
        # only normalize, and if found in english ones then add plural
        header_name = node.data_tokens[0].value
        header_name = header_name.replace("*", "").strip()
        if header_name.lower() in self.EN_SINGULAR_HEADERS:
            header_name += "s"
        if self.uppercase:
            header_name = header_name.upper()
        else:
            header_name = string.capwords(header_name)
        # we only modify header token value in order to preserver optional data driven testing column names
        node.data_tokens[0].value = f"*** {header_name} ***"
        return node

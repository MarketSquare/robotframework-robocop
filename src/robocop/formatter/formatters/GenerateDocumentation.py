from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Template
from jinja2.exceptions import TemplateError
from robot.api.parsing import Documentation, ModelVisitor, Token

from robocop.exceptions import InvalidParameterValueError
from robocop.formatter.formatters import Formatter

if TYPE_CHECKING:
    from robot.parsing.model.blocks import Keyword, TestCaseSection
    from robot.parsing.model.statements import Arguments, Return, ReturnSetting, ReturnStatement

GOOGLE_TEMPLATE = """    Short description.
{% if keyword.arguments|length > 0 %}
{{ formatting.cont_indent }}Args:
{%- for arg in keyword.arguments %}
{{ formatting.cont_indent }}{{ formatting.cont_indent }}{{ arg.name }}: <description>{% endfor %}
{% endif -%}
{% if keyword.returns|length > 0 %}
{{ formatting.cont_indent }}Returns:
{%- for value in keyword.returns %}
{{ formatting.cont_indent }}{{ formatting.cont_indent }}{{ value }}: <description>{% endfor %}
{% endif -%}
"""


class Argument:
    def __init__(self, arg: str):
        if "=" in arg:
            self.name: str
            self.default: str | None
            self.name, self.default = arg.split("=", 1)
        else:
            self.name = arg
            self.default = None
        self.full_name: str = arg

    def __str__(self) -> str:
        return self.full_name


class KeywordData:
    def __init__(self, name: str, arguments: list[Argument], returns: list[str]):
        self.name = name
        self.arguments = arguments
        self.returns = returns


class FormattingData:
    def __init__(self, cont_indent: str, separator: str):
        self.cont_indent = cont_indent
        self.separator = separator


class ArgumentsAndReturnsVisitor(ModelVisitor):  # type: ignore[misc]
    def __init__(self) -> None:
        self.arguments: list[Argument] = []
        self.returns: list[str] = []
        self.doc_exists: bool = False

    def visit_Keyword(self, node: Keyword) -> None:  # noqa: N802
        self.arguments = []
        self.returns = []
        # embedded variables
        for variable in node.header.data_tokens[0].tokenize_variables():
            if variable.type == Token.VARIABLE:
                self.arguments.append(Argument(variable.value))
        self.doc_exists = False
        self.generic_visit(node)

    def visit_Documentation(self, _node: Documentation) -> None:  # noqa: N802
        self.doc_exists = True

    def visit_Arguments(self, node: Arguments) -> None:  # noqa: N802
        if node.errors:
            return
        self.arguments = [Argument(arg) for arg in node.values]

    def visit_ReturnStatement(self, node: ReturnStatement | Return | ReturnSetting) -> None:  # noqa: N802
        if node.errors:
            return
        self.returns = list(node.values)

    visit_Return = visit_ReturnSetting = visit_ReturnStatement  # noqa: N815


class GenerateDocumentation(Formatter):
    """
    Generate keyword documentation with the documentation template.

    By default, GenerateDocumentation uses Google documentation template.
    Following keyword:

    ```robotframework
    *** Keywords ***
    Keyword
        [Arguments]    ${arg}
        ${var}   ${var2}    Step
        RETURN    ${var}    ${var2}
    ```

    will produce following documentation:

    ```robotframework
    *** Keywords ***
    Keyword
        [Documentation]
        ...
        ...    Arguments:
        ...        ${arg}:
        ...
        ...    Returns:
        ...        ${var}
        ...        ${var2}
        [Arguments]    ${arg}
        ${var}   ${var2}    Step
        RETURN    ${var}    ${var2}
    ```

    It is possible to create own template and insert dynamic text like keyword name, argument default values
    or static text (like ``[Documentation]    Documentation stub``). See our docs for more details.

    Generated documentation will be affected by ``NormalizeSeparators`` formatter that's why it is best to
    skip formatting documentation by this formatter:

    ```
    > robocop format --configure GenerateDocumentation.enabled=True
    --configure NormalizeSeparators.skip_documentation=True src
    ```
    """

    ENABLED = False

    WHITESPACE_PATTERN = re.compile(r"(\s{2,}|\t)", re.UNICODE)

    def __init__(self, overwrite: bool = False, doc_template: str = "google", template_directory: str | None = None):
        self.overwrite = overwrite
        self.doc_template = self.load_template(doc_template, template_directory)
        self.args_returns_finder = ArgumentsAndReturnsVisitor()
        super().__init__()

    def visit_TestCaseSection(self, node: TestCaseSection) -> TestCaseSection:  # noqa: N802
        return node

    visit_SettingSection = visit_TestCaseSection  # noqa: N815

    def load_template(self, template: str, template_directory: str | None = None) -> Template:
        try:
            return Template(self.get_template(template, template_directory))
        except TemplateError as err:
            raise InvalidParameterValueError(
                self.__class__.__name__,
                "doc_template",
                "template content",
                f"Failed to load the template: {err}",
            ) from None

    def get_template(self, template: str, template_directory: str | None = None) -> str:
        if template == "google":
            return GOOGLE_TEMPLATE
        template_path = Path(template)
        if not template_path.is_file():
            if not template_path.is_absolute() and template_directory is not None:
                template_path = Path(template_directory) / template_path
            if not template_path.is_file():
                raise InvalidParameterValueError(
                    self.__class__.__name__,
                    "doc_template",
                    template,
                    "The template path does not exist or cannot be found.",
                )
        with open(template_path) as fp:
            return fp.read()

    def visit_Keyword(self, node: Keyword) -> Keyword:  # noqa: N802
        self.args_returns_finder.visit(node)
        if not self.overwrite and self.args_returns_finder.doc_exists:
            return node
        formatting = FormattingData(
            str(self.formatting_config.continuation_indent),  # type: ignore[union-attr]
            str(self.formatting_config.separator),  # type: ignore[union-attr]
        )
        kw_data = KeywordData(node.name, self.args_returns_finder.arguments, self.args_returns_finder.returns)
        generated = self.doc_template.render(keyword=kw_data, formatting=formatting)
        doc_node = self.create_documentation_from_string(generated)
        if self.overwrite:
            self.generic_visit(node)  # remove existing [Documentation]
        node.body.insert(0, doc_node)
        return node

    def visit_Documentation(self, _node: Documentation) -> None:  # noqa: N802
        return None

    def create_documentation_from_string(self, doc_string: str) -> Documentation:
        new_line = [
            Token(Token.EOL),
            Token(Token.SEPARATOR, self.formatting_config.indent),  # type: ignore[union-attr]
            Token(Token.CONTINUATION),
        ]
        tokens = [
            Token(Token.SEPARATOR, self.formatting_config.indent),  # type: ignore[union-attr]
            Token(Token.DOCUMENTATION, "[Documentation]"),
        ]
        for index, line in enumerate(doc_string.splitlines()):
            if index != 0:
                tokens.extend(new_line)
            for value in self.WHITESPACE_PATTERN.split(line):
                if not value:
                    continue
                if value.strip():
                    tokens.append(Token(Token.ARGUMENT, value))
                else:
                    tokens.append(Token(Token.SEPARATOR, value))
        tokens.append(Token(Token.EOL))
        return Documentation(tokens)

from __future__ import annotations

from collections import defaultdict

from robot.api.parsing import Comment, EmptyLine, LibraryImport, Token
from robot.libraries import STDLIBS

from robocop.formatter.disablers import skip_section_if_disabled
from robocop.formatter.exceptions import InvalidParameterValueError
from robocop.formatter.formatters import Formatter


class OrderSettingsSection(Formatter):
    """
    Order settings inside ``*** Settings ***`` section.

    Settings are grouped in following groups:
      - documentation (Documentation, Metadata),
      - imports (Library, Resource, Variables),
      - settings (Suite Setup and Teardown, Test Setup and Teardown, Test Timeout, Test Template),
      - tags (Force Tags, Default Tags, Test Tags)

    Then ordered by groups (according to ``group_order = documentation,imports,settings,tags`` order). Every
    group is separated by ``new_lines_between_groups = 1`` new lines.
    Settings are grouped inside group. Default order can be modified through following parameters:
      - ``documentation_order = documentation,metadata``
      - ``imports_order = preserved``
      - ``settings_order = suite_setup,suite_teardown,test_setup,test_teardown,test_timeout,test_template``

    By default, order of imports is preserved. Read more on configuring this behaviour in the documentation in
    ``Imports order`` section.

    Setting names omitted from custom order will be removed from the file. In following example we are missing metadata
    therefore all metadata will be removed:

    ```
    robocop format --configure OrderSettingsSection.documentation_order=documentation
    ```

    Parsing errors (such as Resources instead of Resource, duplicated settings) are moved to the end of section.
    """

    def __init__(
        self,
        new_lines_between_groups: int = 1,
        group_order: str | None = None,
        documentation_order: str | None = None,
        imports_order: str = "preserved",
        settings_order: str | None = None,
        tags_order: str | None = None,
    ):
        super().__init__()
        self.last_section = None
        self.disabled_group = set()
        self.new_lines_between_groups = new_lines_between_groups
        self.group_order = self.parse_group_order(group_order)
        self.documentation_order = self.parse_order_in_group(
            "documentation",
            documentation_order,
            (Token.DOCUMENTATION, Token.METADATA),
            {"documentation": Token.DOCUMENTATION, "metadata": Token.METADATA},
        )
        self.imports_order = self.parse_order_in_group(
            "imports",
            imports_order,
            (Token.LIBRARY, Token.RESOURCE, Token.VARIABLES),
            {
                "library": Token.LIBRARY,
                "resource": Token.RESOURCE,
                "variables": Token.VARIABLES,
            },
        )
        self.settings_order = self.parse_order_in_group(
            "settings",
            settings_order,
            (
                Token.SUITE_SETUP,
                Token.SUITE_TEARDOWN,
                Token.TEST_SETUP,
                Token.TEST_TEARDOWN,
                Token.TEST_TIMEOUT,
                Token.TEST_TEMPLATE,
            ),
            {
                "suite_setup": Token.SUITE_SETUP,
                "suite_teardown": Token.SUITE_TEARDOWN,
                "test_setup": Token.TEST_SETUP,
                "test_teardown": Token.TEST_TEARDOWN,
                "test_timeout": Token.TEST_TIMEOUT,
                "test_template": Token.TEST_TEMPLATE,
            },
        )
        self.tags_order = self.parse_order_in_group(
            "tags",
            tags_order,
            (Token.FORCE_TAGS, Token.DEFAULT_TAGS),
            {"force_tags": Token.FORCE_TAGS, "test_tags": Token.FORCE_TAGS, "default_tags": Token.DEFAULT_TAGS},
        )

    def parse_group_order(self, order):
        default = ("documentation", "imports", "settings", "tags")
        if order is None:
            return default
        if not order:
            return []
        parts = order.lower().split(",")
        if any(part not in default for part in parts):
            raise InvalidParameterValueError(
                self.__class__.__name__,
                "group_order",
                order,
                f"Custom order should be provided in comma separated list with valid group names:\n{default}",
            )
        return parts

    def parse_order_in_group(self, name, order, default, mapping):
        if order is None:
            return default
        if not order:
            return []
        if order == "preserved":
            self.disabled_group.add(name)
            return default
        parts = order.lower().split(",")
        try:
            return [mapping[part] for part in parts]
        except KeyError:
            raise InvalidParameterValueError(
                self.__class__.__name__,
                "order",
                order,
                f"Custom order should be provided in comma separated list with valid group names:\n"
                f"{sorted(mapping.keys())}",
            ) from None

    def visit_File(self, node):  # noqa: N802
        self.last_section = node.sections[-1] if node.sections else None
        return self.generic_visit(node)

    @skip_section_if_disabled
    def visit_SettingSection(self, node):  # noqa: N802
        if not node.body:
            return None
        if node is self.last_section and not isinstance(node.body[-1], EmptyLine):
            node.body[-1] = self.fix_eol(node.body[-1])
        comments, errors = [], []
        groups = defaultdict(list)
        for child in node.body:
            child_type = getattr(child, "type", None)
            if isinstance(child, Comment):
                comments.append(child)
            elif child_type in self.documentation_order:
                groups["documentation"].append((comments, child))
                comments = []
            elif child_type in self.imports_order:
                groups["imports"].append((comments, child))
                comments = []
            elif child_type in self.settings_order:
                groups["settings"].append((comments, child))
                comments = []
            elif child_type in self.tags_order:
                groups["tags"].append((comments, child))
                comments = []
            elif not isinstance(child, EmptyLine):
                errors.append(child)

        group_map = {
            "documentation": self.documentation_order,
            "imports": self.imports_order,
            "settings": self.settings_order,
            "tags": self.tags_order,
        }

        new_body = []
        empty_line = EmptyLine.from_params(eol="\n")
        order_of_groups = [group for group in self.group_order if group in groups]
        last_index = len(order_of_groups) - 1
        for index, group in enumerate(order_of_groups):
            unordered = groups[group]
            if group in self.disabled_group:
                for comment_lines, child in unordered:
                    new_body.extend(comment_lines)
                    new_body.append(child)
            else:
                if group == "imports":
                    unordered = self.sort_builtin_libs(unordered)
                order = group_map[group]
                for token_type in order:
                    for comment_lines, child in unordered:
                        if child.type == token_type:
                            new_body.extend(comment_lines)
                            new_body.append(child)
            if index != last_index:
                new_body.extend([empty_line] * self.new_lines_between_groups)

        # not recognized headers, parsing errors like Resources instead of Resource
        if errors:
            new_body.extend([empty_line] * self.new_lines_between_groups)
            new_body.extend(errors)
        new_body.extend(comments)
        if node is not self.last_section:
            new_body.append(empty_line)
        node.body = new_body
        return node

    @staticmethod
    def fix_eol(node):
        if not getattr(node, "tokens", None):
            return node
        if getattr(node.tokens[-1], "type", None) != Token.EOL:
            return node
        node.tokens[-1].value = "\n"
        return node

    @staticmethod
    def sort_builtin_libs(statements):
        before, after = [], []
        for comments, statement in statements:
            if (
                isinstance(statement, LibraryImport)
                and statement.name
                and statement.name in STDLIBS
                and statement.name != "Remote"
            ):
                before.append((comments, statement))
            else:
                after.append((comments, statement))
        before = sorted(before, key=lambda x: x[1].name)
        return before + after

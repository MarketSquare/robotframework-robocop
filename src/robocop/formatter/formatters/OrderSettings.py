from robot.api.parsing import Comment, EmptyLine, Token

from robocop.formatter.disablers import skip_if_disabled, skip_section_if_disabled
from robocop.formatter.exceptions import InvalidParameterValueError, RobocopConfigError
from robocop.formatter.formatters import Formatter


class InvalidSettingsOrderError(InvalidParameterValueError):
    def __init__(self, formatter, param_name, param_value, valid_values):
        valid_names = ",".join(sorted(valid_values.keys()))
        msg = f"Custom order should be provided in comma separated list with valid setting names: {valid_names}"
        super().__init__(formatter, param_name, param_value, msg)


class DuplicateInSettingsOrderError(InvalidParameterValueError):
    def __init__(self, formatter, param_name, param_value):
        provided_order = ",".join(param.lower() for param in param_value)
        msg = "Custom order cannot contain duplicated setting names."
        super().__init__(formatter, param_name, provided_order, msg)


class SettingInBothOrdersError(RobocopConfigError):
    def __init__(self, formatter, first_order, second_order, duplicates):
        names = ",".join(setting.lower() for setting in duplicates)
        msg = (
            f"{formatter}: Invalid '{first_order}' and '{second_order}' order values. "
            f"Following setting names exists in both orders: {names}"
        )
        super().__init__(msg)


class OrderSettings(Formatter):
    """
    Order settings like ``[Arguments]``, ``[Setup]``, ``[Return]`` inside Keywords and Test Cases.

    Keyword settings ``[Documentation]``, ``[Tags]``, ``[Timeout]``, ``[Arguments]`` are put before keyword body and
    settings like ``[Teardown]``, ``[Return]`` are moved to the end of the keyword:

    ```robotframework
    *** Keywords ***
    Keyword
        [Teardown]  Keyword
        [Return]  ${value}
        [Arguments]  ${arg}
        [Documentation]  this is
        ...    doc
        [Tags]  sanity
        Pass
    ```

    To:
    ```robotframework
    *** Keywords ***
    Keyword
        [Documentation]  this is
        ...    doc
        [Tags]  sanity
        [Arguments]  ${arg}
        Pass
        [Teardown]  Keyword
        [Return]  ${value}
    ```

    Test case settings ``[Documentation]``, ``[Tags]``, ``[Template]``, ``[Timeout]``, ``[Setup]`` are put before
    test case body and ``[Teardown]`` is moved to the end of test case.

    Default order can be changed using following parameters:
      - ``keyword_before = documentation,tags,timeout,arguments``
      - ``keyword_after = teardown,return``
      - ``test_before = documentation,tags,template,timeout,setup``
      - ``test_after = teardown``

    Not all settings names need to be passed to given parameter. Missing setting names are not ordered. Example::

        robocop format -c OrderSettings.keyword_before= -c OrderSettings.keyword_after=

    It will order only test cases because all setting names for keywords are missing.
    """

    KEYWORD_SETTINGS = {
        "documentation": Token.DOCUMENTATION,
        "tags": Token.TAGS,
        "arguments": Token.ARGUMENTS,
        "timeout": Token.TIMEOUT,
        "setup": Token.SETUP,
        "return": Token.RETURN,
        "teardown": Token.TEARDOWN,
    }
    TEST_SETTINGS = {
        "documentation": Token.DOCUMENTATION,
        "tags": Token.TAGS,
        "timeout": Token.TIMEOUT,
        "template": Token.TEMPLATE,
        "setup": Token.SETUP,
        "teardown": Token.TEARDOWN,
    }

    def __init__(
        self,
        keyword_before: str = "documentation,tags,arguments,timeout,setup",
        keyword_after: str = "teardown,return",
        test_before: str = "documentation,tags,template,timeout,setup",
        test_after: str = "teardown",
    ):
        super().__init__()
        self.keyword_before = self.get_order(keyword_before, "keyword_before", self.KEYWORD_SETTINGS)
        self.keyword_after = self.get_order(keyword_after, "keyword_after", self.KEYWORD_SETTINGS)
        self.test_before = self.get_order(test_before, "test_before", self.TEST_SETTINGS)
        self.test_after = self.get_order(test_after, "test_after", self.TEST_SETTINGS)
        self.all_keyword_settings = {*self.keyword_before, *self.keyword_after}
        self.all_test_settings = {*self.test_before, *self.test_after}
        self.assert_no_duplicates_in_orders()

    def get_order(self, order, param_name, name_map):
        if not order:
            return []
        parts = order.lower().split(",")
        try:
            return [name_map[part] for part in parts]
        except KeyError:
            raise InvalidSettingsOrderError(self.__class__.__name__, param_name, order, name_map) from None

    def assert_no_duplicates_in_orders(self):
        """Check if settings are not duplicated in after/before section and in the same section itself."""
        orders = {
            "keyword_before": set(self.keyword_before),
            "keyword_after": set(self.keyword_after),
            "test_before": set(self.test_before),
            "test_after": set(self.test_after),
        }
        # check if there is no duplicate in single order, ie test_after=setup,setup
        for name, order_set in orders.items():
            if len(self.__dict__[name]) != len(order_set):
                raise DuplicateInSettingsOrderError(self.__class__.__name__, name, self.__dict__[name])
        # check if there is no duplicate in opposite orders, ie test_before=tags test_after=tags
        shared_keyword = orders["keyword_before"].intersection(orders["keyword_after"])
        shared_test = orders["test_before"].intersection(orders["test_after"])
        if shared_keyword:
            raise SettingInBothOrdersError(self.__class__.__name__, "keyword_before", "keyword_after", shared_keyword)
        if shared_test:
            raise SettingInBothOrdersError(self.__class__.__name__, "test_before", "test_after", shared_test)

    @skip_section_if_disabled
    def visit_Section(self, node):  # noqa: N802
        return self.generic_visit(node)

    @skip_if_disabled
    def visit_Keyword(self, node):  # noqa: N802
        return self.order_settings(node, self.all_keyword_settings, self.keyword_before, self.keyword_after)

    @skip_if_disabled
    def visit_TestCase(self, node):  # noqa: N802
        return self.order_settings(node, self.all_test_settings, self.test_before, self.test_after)

    def order_settings(self, node, setting_types, before, after):
        if not node.body:
            return node
        settings = {}
        not_settings, trailing_after = [], []
        after_seen = False
        # when after_seen is set to True then all statements go to trailing_after and last non data
        # will be appended after tokens defined in `after` set (like [Return])
        comments, header_line = [], []
        for child in node.body:
            if isinstance(child, Comment):
                if child.lineno == node.lineno:  # comment in the same line as test/kw name
                    header_line.append(child)
                else:
                    comments.append(child)
            elif getattr(child, "type", "invalid") in setting_types:
                after_seen = after_seen or child.type in after
                settings[child.type] = (comments, child)
                comments = []
            elif after_seen:
                trailing_after.extend(comments)
                comments = []
                trailing_after.append(child)
            else:
                not_settings.extend(comments)
                comments = []
                not_settings.append(child)
        trailing_after.extend(comments)
        # comments after last data statement are considered as comment outside body
        trailing_non_data = []
        while trailing_after and isinstance(trailing_after[-1], (EmptyLine, Comment)):
            trailing_non_data.insert(0, trailing_after.pop())
        not_settings += trailing_after
        node.body = (
            header_line
            + self.add_in_order(before, settings)
            + not_settings
            + self.add_in_order(after, settings)
            + trailing_non_data
        )
        return node

    @staticmethod
    def add_in_order(order, settings_in_node):
        nodes = []
        for token_type in order:
            if token_type not in settings_in_node:
                continue
            comments, node = settings_in_node[token_type]
            nodes.extend(comments)
            nodes.append(node)
        return nodes

import ast
import re
from collections import Counter

from robot.api.parsing import Token, Variable

from robocop.formatter.disablers import skip_if_disabled, skip_section_if_disabled
from robocop.formatter.exceptions import InvalidParameterValueError
from robocop.formatter.formatters import Formatter
from robocop.formatter.skip import Skip


class NormalizeAssignments(Formatter):
    """
    Normalize assignments.

    It can change all assignment signs to either the most commonly used in a given file or a configured fixed one.
    Default behaviour is autodetect for assignments from Keyword Calls and removing assignment signs in
    *** Variables *** section. It can be freely configured.

    In this code most common is no equal sign at all. We should remove `=` signs from all lines:

    ```robotframework
    *** Variables ***
    ${var} =  ${1}
    @{list}  a
    ...  b
    ...  c

    ${variable}=  10


    *** Keywords ***
    Keyword
        ${var}  Keyword1
        ${var}   Keyword2
        ${var}=    Keyword
    ```

    To:

    ```robotframework
    *** Variables ***
    ${var}  ${1}
    @{list}  a
    ...  b
    ...  c

    ${variable}  10


    *** Keywords ***
    Keyword
        ${var}  Keyword1
        ${var}   Keyword2
        ${var}    Keyword
    ```

    You can configure that behaviour to automatically add desired equal sign with `equal_sign_type`
    (default `autodetect`) and `equal_sign_type_variables` (default `remove`) parameters.
    (possible types are: `autodetect`, `remove`, `equal_sign` ('='), `space_and_equal_sign` (' =').
    """

    HANDLES_SKIP = frozenset({"skip_sections"})

    def __init__(
        self, equal_sign_type: str = "autodetect", equal_sign_type_variables: str = "remove", skip: Skip = None
    ):
        super().__init__(skip)
        self.remove_equal_sign = re.compile(r"\s?=$")
        self.file_equal_sign_type = None
        self.file_equal_sign_type_variables = None
        self.equal_sign_type = self.parse_equal_sign_type(equal_sign_type, "equal_sign_type")
        self.equal_sign_type_variables = self.parse_equal_sign_type(
            equal_sign_type_variables, "equal_sign_type_variables"
        )

    def parse_equal_sign_type(self, value, name):
        types = {
            "remove": "",
            "equal_sign": "=",
            "space_and_equal_sign": " =",
            "autodetect": None,
        }
        if value not in types:
            raise InvalidParameterValueError(
                self.__class__.__name__,
                value,
                name,
                "Possible values:\n    remove\n    equal_sign\n    space_and_equal_sign",
            )
        return types[value]

    def visit_File(self, node):  # noqa: N802
        """
        If no assignment sign was set the file will be scanned to find most common assignment sign.

        This auto-detection will happen for every file separately.
        """
        if self.equal_sign_type is None or self.equal_sign_type_variables is None:
            common, common_variables = self.auto_detect_equal_sign(node)
            if self.equal_sign_type is None and common is not None:
                self.file_equal_sign_type = common
            if self.equal_sign_type_variables is None and common_variables is not None:
                self.file_equal_sign_type_variables = common_variables
            if self.file_equal_sign_type is None and self.file_equal_sign_type_variables is None:
                return node
        self.generic_visit(node)
        self.file_equal_sign_type = None
        self.file_equal_sign_type_variables = None
        return node

    @skip_section_if_disabled
    def visit_Section(self, node):  # noqa: N802
        return self.generic_visit(node)

    @skip_if_disabled
    def visit_KeywordCall(self, node):  # noqa: N802
        if node.assign:  # if keyword returns any value
            assign_tokens = node.get_tokens(Token.ASSIGN)
            self.normalize_equal_sign(assign_tokens[-1], self.equal_sign_type, self.file_equal_sign_type)
        return node

    def visit_VariableSection(self, node):  # noqa: N802
        for child in node.body:
            if not isinstance(child, Variable):
                continue
            if self.disablers.is_node_disabled("NormalizeAssignments", child):
                continue
            var_token = child.get_token(Token.VARIABLE)
            self.normalize_equal_sign(
                var_token,
                self.equal_sign_type_variables,
                self.file_equal_sign_type_variables,
            )
        return node

    def normalize_equal_sign(self, token, overwrite, local_normalize):
        token.value = re.sub(self.remove_equal_sign, "", token.value)
        if overwrite:
            token.value += overwrite
        elif local_normalize:
            token.value += local_normalize

    @staticmethod
    def auto_detect_equal_sign(node):
        auto_detector = AssignmentTypeDetector()
        auto_detector.visit(node)
        return auto_detector.most_common, auto_detector.most_common_variables


class AssignmentTypeDetector(ast.NodeVisitor):
    def __init__(self):
        self.sign_counter, self.sign_counter_variables = Counter(), Counter()
        self.most_common = None
        self.most_common_variables = None

    def visit_File(self, node):  # noqa: N802
        self.generic_visit(node)
        if len(self.sign_counter) >= 2:
            self.most_common = self.sign_counter.most_common(1)[0][0]
        if len(self.sign_counter_variables) >= 2:
            self.most_common_variables = self.sign_counter_variables.most_common(1)[0][0]

    def visit_KeywordCall(self, node):  # noqa: N802
        if node.assign:  # if keyword returns any value
            sign = self.get_assignment_sign(node.assign[-1])
            self.sign_counter[sign] += 1

    def visit_VariableSection(self, node):  # noqa: N802
        for child in node.body:
            if not isinstance(child, Variable):
                continue
            var_token = child.get_token(Token.VARIABLE)
            sign = self.get_assignment_sign(var_token.value)
            self.sign_counter_variables[sign] += 1
        return node

    @staticmethod
    def get_assignment_sign(token_value):
        return token_value[token_value.find("}") + 1 :]

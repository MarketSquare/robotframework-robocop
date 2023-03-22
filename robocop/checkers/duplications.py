"""
Duplications checkers
"""
from collections import defaultdict

from robot.api import Token

from robocop.checkers import VisitorChecker
from robocop.rules import Rule, RuleParam, RuleSeverity
from robocop.utils import get_errors, normalize_robot_name, normalize_robot_var_name


def configure_sections_order(value):
    section_map = {
        "settings": Token.SETTING_HEADER,
        "variables": Token.VARIABLE_HEADER,
        "testcase": Token.TESTCASE_HEADER,
        "testcases": Token.TESTCASE_HEADER,
        "task": "TASK HEADER",
        "tasks": "TASK HEADER",
        "keyword": Token.KEYWORD_HEADER,
        "keywords": Token.KEYWORD_HEADER,
    }
    sections_order = {}
    for index, name in enumerate(value.split(",")):
        if name.lower() not in section_map or section_map[name.lower()] in sections_order:
            raise ValueError(f"Invalid section name: `{name}`")
        sections_order[section_map[name.lower()]] = index
    if Token.TESTCASE_HEADER in sections_order:
        sections_order["TASK HEADER"] = sections_order[Token.TESTCASE_HEADER]
    return sections_order


rules = {
    "0801": Rule(
        rule_id="0801",
        name="duplicated-test-case",
        msg="Multiple test cases with name '{{ name }}' (first occurrence in line {{ first_occurrence_line }})",
        severity=RuleSeverity.ERROR,
        docs="""
        It is not allowed to reuse the same name of the test case within the same suite in Robot Framework. 
        Name matching is case-insensitive and ignores spaces and underscore characters.
        Duplicated test cases example::
        
            *** Test Cases ***
            Test with name
                No Operation
            
            test_with Name  # it is a duplicate of 'Test with name'
                No Operation
        """,
    ),
    "0802": Rule(
        rule_id="0802",
        name="duplicated-keyword",
        msg="Multiple keywords with name '{{ name }}' (first occurrence in line {{ first_occurrence_line }})",
        severity=RuleSeverity.ERROR,
        docs="""
        Do not define keywords with the same name inside the same file. Name matching is case-insensitive and 
        ignores spaces and underscore characters.
        Duplicated keyword names example::
        
            *** Keywords ***
            Keyword
                No Operation
            
            keyword
                No Operation
            
            K_eywor d
                No Operation
            
        """,
    ),
    "0803": Rule(
        rule_id="0803",
        name="duplicated-variable",
        msg="Multiple variables with name '{{ name }}' in Variables section (first occurrence in line "
        "{{ first_occurrence_line }}). "
        "Note that Robot Framework is case-insensitive",
        severity=RuleSeverity.ERROR,
        docs="""
        Variable names in Robot Framework are case-insensitive and ignore spaces and underscores. Following variables 
        are duplicates::
        
            *** Variables ***
            ${variable}    1
            ${VARIAble}    a
            @{variable}    a  b
            ${v ariabl e}  c
            ${v_ariable}   d

        """,
    ),
    "0804": Rule(
        rule_id="0804",
        name="duplicated-resource",
        msg="Multiple resource imports with path '{{ name }}' (first occurrence in line {{ first_occurrence_line }})",
        severity=RuleSeverity.WARNING,
    ),
    "0805": Rule(
        rule_id="0805",
        name="duplicated-library",
        msg="Multiple library imports with name '{{ name }}' and identical arguments (first occurrence in line "
        "{{ first_occurrence_line }})",
        severity=RuleSeverity.WARNING,
        docs="""
        If you need to reimport library use alias::
        
            *** Settings ***
            Library  RobotLibrary
            Library  RobotLibrary  AS  OtherRobotLibrary

        """,
    ),
    "0806": Rule(
        rule_id="0806",
        name="duplicated-metadata",
        msg="Duplicated metadata '{{ name }}' (first occurrence in line {{ first_occurrence_line }})",
        severity=RuleSeverity.WARNING,
    ),
    "0807": Rule(
        rule_id="0807",
        name="duplicated-variables-import",
        msg="Duplicated variables import with path '{{ name }}' (first occurrence in line {{ first_occurrence_line }})",
        severity=RuleSeverity.WARNING,
    ),
    "0808": Rule(
        rule_id="0808",
        name="section-already-defined",
        msg="'{{ section_name }}' section header already defined in file (first occurrence in line "
        "{{ first_occurrence_line }})",
        severity=RuleSeverity.WARNING,
        docs="""
        Duplicated section in the file. Robot Framework will handle repeated sections but it is recommended to not 
        duplicate them.
        
        Example::
        
            *** Test Cases ***
            My Test
                Keyword
            
            *** Keywords ***
            Keyword
                No Operation
            
            *** Test Cases ***  # duplicate
            Other Test
                Keyword

        """,
    ),
    "0809": Rule(
        RuleParam(
            name="sections_order",
            default="settings,variables,testcases,keywords",
            converter=configure_sections_order,
            show_type="str",
            desc="order of sections in comma-separated list",
        ),
        rule_id="0809",
        name="section-out-of-order",
        msg="'{{ section_name }}' section header is defined in wrong order: {{ recommended_order }}",
        severity=RuleSeverity.WARNING,
        docs="""
        Sections should be defined in order set by `sections_order` 
        parameter (default: `settings,variables,testcases,keywords`).
        
        To change the default order use following option::
        
            robocop --configure section-out-of-order:sections_order:comma,separated,list,of,sections
        
        where section should be case-insensitive name from the list: comments, settings, variables, testcases, keywords. 
        Order of not configured sections is ignored.
        
        Example::
        
            *** Settings ***
            
            *** Keywords ***
            
            *** Test Cases ***  # it will report issue because Test Cases should be defined before Keywords

        """,
    ),
    "0810": Rule(
        rule_id="0810",
        name="both-tests-and-tasks",
        msg="Both Task(s) and Test Case(s) section headers defined in file",
        severity=RuleSeverity.ERROR,
        docs="""
        The file contains both Test Case and Task sections. Use only one of them. ::
        
            *** Test Cases ***
            
            *** Tasks ***

        """,
    ),
    "0811": Rule(
        rule_id="0811",
        name="duplicated-argument-name",
        msg="Argument name '{{ argument_name }}' is already used",
        severity=RuleSeverity.ERROR,
        docs="""
        Variable names in Robot Framework are case-insensitive and ignores spaces and underscores. Following arguments 
        are duplicates::
        
            *** Keywords ***
            Keyword
                [Arguments]    ${var}  ${VAR}  ${v_ar}  ${v ar}
                Other Keyword

        """,
    ),
    "0812": Rule(
        rule_id="0812",
        name="duplicated-assigned-var-name",
        msg="Assigned variable name '{{ variable_name }}' is already used",
        severity=RuleSeverity.INFO,
        docs="""
        Variable names in Robot Framework are case-insensitive and ignores spaces and underscores. Following variables 
        are duplicates::
        
            *** Test Cases ***
            Test
                ${var}  ${VAR}  ${v_ar}  ${v ar}  Keyword
        
        """,
    ),
    "0813": Rule(
        rule_id="0813",
        name="duplicated-setting",
        msg="{{ error_msg }}",
        severity=RuleSeverity.WARNING,
        docs="""
        Some settings can be used only once in a file. Only the first value is used.
        Example::
        
            *** Settings ***
            Force Tags        F1
            Force Tags        F2  # this setting will be ignored
        
        """,
    ),
}


class DuplicationsChecker(VisitorChecker):
    """Checker for duplicated names."""

    reports = (
        "duplicated-test-case",
        "duplicated-keyword",
        "duplicated-variable",
        "duplicated-resource",
        "duplicated-library",
        "duplicated-metadata",
        "duplicated-variables-import",
        "duplicated-argument-name",
        "duplicated-assigned-var-name",
        "duplicated-setting",
    )

    def __init__(self):
        self.test_cases = defaultdict(list)
        self.keywords = defaultdict(list)
        self.variables = defaultdict(list)
        self.resources = defaultdict(list)
        self.libraries = defaultdict(list)
        self.metadata = defaultdict(list)
        self.variable_imports = defaultdict(list)
        super().__init__()

    def visit_File(self, node):  # noqa
        self.test_cases = defaultdict(list)
        self.keywords = defaultdict(list)
        self.variables = defaultdict(list)
        self.resources = defaultdict(list)
        self.libraries = defaultdict(list)
        self.metadata = defaultdict(list)
        self.variable_imports = defaultdict(list)
        super().visit_File(node)
        self.check_duplicates(self.test_cases, "duplicated-test-case")
        self.check_duplicates(self.keywords, "duplicated-keyword")
        self.check_duplicates(self.variables, "duplicated-variable")
        self.check_duplicates(self.resources, "duplicated-resource", True)
        self.check_duplicates(self.metadata, "duplicated-metadata", True)
        self.check_duplicates(self.variable_imports, "duplicated-variables-import", True)
        self.check_library_duplicates(self.libraries, "duplicated-library")

    def check_duplicates(self, container, rule, underline_whole_line=False):
        for nodes in container.values():
            for duplicate in nodes[1:]:
                if underline_whole_line:
                    end_col = duplicate.end_col_offset + 1
                else:
                    end_col = duplicate.col_offset + len(duplicate.name) + 1
                self.report(
                    rule, name=duplicate.name, first_occurrence_line=nodes[0].lineno, node=duplicate, end_col=end_col
                )

    def check_library_duplicates(self, container, rule):
        for nodes in container.values():
            for duplicate in nodes[1:]:
                lib_token = duplicate.get_token(Token.NAME)
                self.report(
                    rule,
                    name=duplicate.name,
                    first_occurrence_line=nodes[0].lineno,
                    node=duplicate,
                    col=lib_token.col_offset + 1,
                    end_col=lib_token.end_col_offset + 1,
                )

    def visit_TestCase(self, node):  # noqa
        testcase_name = normalize_robot_name(node.name)
        self.test_cases[testcase_name].append(node)
        self.generic_visit(node)

    def visit_Keyword(self, node):  # noqa
        keyword_name = normalize_robot_name(node.name)
        self.keywords[keyword_name].append(node)
        self.generic_visit(node)

    def visit_KeywordCall(self, node):  # noqa
        assign = node.get_tokens(Token.ASSIGN)
        seen = set()
        for var in assign:
            name = normalize_robot_var_name(var.value)
            if name in seen:
                self.report(
                    "duplicated-assigned-var-name",
                    variable_name=var.value,
                    node=node,
                    lineno=var.lineno,
                    col=var.col_offset + 1,
                    end_col=var.col_offset + len(var.value) + 1,
                )
            else:
                seen.add(name)

    def visit_VariableSection(self, node):  # noqa
        self.generic_visit(node)

    def visit_Variable(self, node):  # noqa
        if not node.name or get_errors(node):
            return
        var_name = normalize_robot_name(self.replace_chars(node.name, "${}@&"))
        self.variables[var_name].append(node)

    @staticmethod
    def replace_chars(name, chars):
        return "".join(c for c in name if c not in chars)

    def visit_ResourceImport(self, node):  # noqa
        if node.name:
            self.resources[node.name].append(node)

    def visit_LibraryImport(self, node):  # noqa
        if not node.name:
            return
        lib_name = node.alias if node.alias else node.name
        name_with_args = lib_name + "".join(token.value for token in node.get_tokens(Token.ARGUMENT))
        self.libraries[name_with_args].append(node)

    def visit_Metadata(self, node):  # noqa
        if node.name is not None:
            self.metadata[node.name + node.value].append(node)

    def visit_VariablesImport(self, node):  # noqa
        if not node.name:
            return
        # only python files can have arguments - covered in E0404 variables-import-with-args
        if not node.name.endswith(".py") and node.get_token(Token.ARGUMENT):
            return
        name_with_args = node.name + "".join(token.value for token in node.data_tokens[2:])
        self.variable_imports[name_with_args].append(node)

    def visit_Arguments(self, node):  # noqa
        args = set()
        for arg in node.get_tokens(Token.ARGUMENT):
            orig, *_ = arg.value.split("=", maxsplit=1)
            name = normalize_robot_var_name(orig)
            if name in args:
                self.report(
                    "duplicated-argument-name",
                    argument_name=orig,
                    node=node,
                    lineno=arg.lineno,
                    col=arg.col_offset + 1,
                    end_col=arg.col_offset + len(orig) + 1,
                )
            else:
                args.add(name)

    def visit_Error(self, node):  # noqa
        for error in get_errors(node):
            if "is allowed only once" in error:
                self.report(
                    "duplicated-setting", error_msg=error, node=node, end_col=node.data_tokens[0].end_col_offset
                )


class SectionHeadersChecker(VisitorChecker):
    """Checker for duplicated or out of order section headers."""

    reports = (
        "section-already-defined",
        "section-out-of-order",
        "both-tests-and-tasks",
    )

    def __init__(self):
        self.sections_by_order = []
        self.sections_by_existence = dict()
        super().__init__()

    @staticmethod
    def section_order_to_str(order):
        by_index = sorted([(key, value) for key, value in order.items()], key=lambda x: x[1])
        name_map = {
            Token.SETTING_HEADER: "Settings",
            Token.VARIABLE_HEADER: "Variables",
            Token.TESTCASE_HEADER: "Test Cases / Tasks",
            "TASK HEADER": "Test Cases / Tasks",
            Token.KEYWORD_HEADER: "Keywords",
        }
        order_str = []
        for name, _ in by_index:
            mapped_name = name_map[name]
            if mapped_name not in order_str:
                order_str.append(mapped_name)
        return " > ".join(order_str)

    def visit_File(self, node):  # noqa
        self.sections_by_order = []
        self.sections_by_existence = dict()
        super().visit_File(node)

    def visit_SectionHeader(self, node):  # noqa
        section_name = node.type
        if section_name not in self.param("section-out-of-order", "sections_order"):
            return
        if section_name in (Token.TESTCASE_HEADER, "TASK HEADER"):
            # a bit awkward implementation because before RF 6.0 task header used TESTCASE_HEADER type
            if "task" in node.name.lower():
                section_name = "TASK HEADER"
                if Token.TESTCASE_HEADER in self.sections_by_existence:
                    self.report("both-tests-and-tasks", node=node, col=node.col_offset + 1, end_col=node.end_col_offset)
            else:
                if "TASK HEADER" in self.sections_by_existence:
                    self.report("both-tests-and-tasks", node=node, col=node.col_offset + 1, end_col=node.end_col_offset)
        order_id = self.param("section-out-of-order", "sections_order")[section_name]
        if section_name in self.sections_by_existence:
            self.report(
                "section-already-defined",
                section_name=node.data_tokens[0].value,
                first_occurrence_line=self.sections_by_existence[section_name],
                node=node,
                end_col=node.end_col_offset,
            )
        else:
            self.sections_by_existence[section_name] = node.lineno
        if any(previous_id > order_id for previous_id in self.sections_by_order):
            token = node.data_tokens[0]
            self.report(
                "section-out-of-order",
                section_name=token.value,
                recommended_order=self.section_order_to_str(self.param("section-out-of-order", "sections_order")),
                node=node,
                end_col=token.end_col_offset + 1,
            )
        self.sections_by_order.append(order_id)

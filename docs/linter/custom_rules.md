# Custom rules

## How to include custom rules

You can include your own custom rules with ``--custom-rules`` option.
It accepts a list of paths to files, directories or name of the Python module. Example:

=== ":octicons-command-palette-24: cli"

    ```
    robocop check --custom-rules my/own/rule.py --custom-rules custom_rules.py
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    custom_rules = [
        "my/own/rule.py",
        "custom_rules.py"
    ]
    ```

## How to write custom rules

Writing your own rules requires implementing the following:

1. Rule class, which describes what code issue we are looking for and how it will be reported
2. Checker class, which scans the code and reports code issues.

Custom rule class inherits from Robocop ``Rule`` class and must override the following attributes:

- ``name`` (rule name)
- ``rule_id``
- ``message``
- ``severity``
- ``__doc__`` (class documentation that will be used as rule documentation)

It can optionally override the following attributes:

- ``severity_threshold``
- ``version`` (supported Robot Framework version, for example ``>=6``)
- ``enabled`` (default ``True``, can be used to define rules disabled by default)
- ``deprecated`` (set to ``True`` to deprecate rule)
- ``parameters``

For reference, you may look at existing rules in the Robocop.

Example rule definition:

```python title="rule definition"
from robocop.linter.rules import (
    Rule,
    RuleParam,
    RuleSeverity
)

class ArgumentsPerLineRule(Rule):
    """
    Rule description and documentation.

    Supports Markdown.
    """

    name = "rule-name"
    rule_id = "GROUP01"
    message = "Rule message"
    severity = RuleSeverity.INFO
    parameters = [
        RuleParam(
            name="parameter_name",
            default=1,
            converter=int,
            desc="Parameter which will be converted to integer",
        ),
    ]
```

This rule can be used by checker class. Checker class can inherit from one of the following:

- ``VisitorChecker`` which visits Robot Framework code using ast
- ``RawFileChecker`` which scans every line (without parsing code as Robot Framework code)

Each checker class should define which rules it uses as class attribute and rule class as a type. For example:

```python title="example.py"
from robocop.linter.rules import (
    Rule,
    RuleParam,
    RuleSeverity,
    VisitorChecker
)


class ExampleTestCaseRule(Rule):
    """
    Check if there is 'Example' in the test case name.
    """

    name = "example-in-name"
    rule_id = "EX01"
    message = "There is 'Example' in test case name"
    severity = RuleSeverity.WARNING


class NoExamplesChecker(VisitorChecker):
    example_in_name: ExampleTestCaseRule

    def visit_TestCaseName(self, node):  # noqa: N802
        if 'Example' in node.name:
            self.report(self.example_in_name, node=node, col=node.name.find('Example'))
```

## Issue position

When reporting an issue, you need to specify the position of the issue in the source code. ``report()`` method only
requires ``node`` argument, which can be used to determine the position of the issue. But it is recommended to pass
more detailed information (for example, ``lineno``, ``end_lineno``, ``col``, ``end_col``) to ``report()`` method.

Verify if the reported position is not exceeding physical locations. Some reporters may not be able to handle incorrect
positions. For example, ``SonarQube`` platform requires strictly correct reports and may fail to parse the whole file.

## Rule parameters

Rules can have configurable values. You need to specify them using the RuleParam class and pass it as an argument to Rule:

```python title="example.py"
from robocop.linter.rules import (
    Rule,
    RuleParam,
    RuleSeverity,
    VisitorChecker
)


class ExampleTestCaseRule(Rule):
    """
    Check if there is a parametrised substring in the test case name.
    """

    name = "example-in-name"
    rule_id = "EX01"
    message = "There is '{variable}' in test case name"
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(
            name="param_name",
            default="Example",
            converter=str,
            desc="Optional desc",
        ),
    ]


class NoExamplesChecker(VisitorChecker):
    example_in_name: ExampleTestCaseRule

    def visit_TestCaseName(self, node):  # noqa: N802
        if self.example_in_name.param_name in node.name:
            self.report(
                self.example_in_name,
                variable=self.example_in_name.param_name,
                node=node,
                col=node.name.find(self.example_in_name.param_name))

```

Configurable parameter can be referred by its ``name`` in command line options:

=== ":octicons-command-palette-24: cli"

    ```
    robocop check --custom-rules my/own/rule.py --configure example-in-name.param_name=AnotherExample
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    custom_rules = [
        "my/own/rule.py"
    ]
    configure = [
        "example-in-name.param_name=AnotherExample"
    ]
    ```

The value of the configurable parameter can be retrieved by using attribute access:

```python
self.name_of_the_rule.name_of_param
```

Parameter value is passed as string. Use ``converter`` argument to define a method that will be used to convert the value:

```python
RuleParam(name="int_param", converter=int, default=10, desc="Optional desc")  # convert str to int
# my_own_method will be called with a custom_param value
RuleParam(name="custom_param", converter=my_own_method, default="custom", desc="Optional desc")
```

## Templated rule messages

When defining rule messages, you can use Python string formatting to supply dynamic values to a rule message:

```python
message = "There is '{variable}' in test case name"
```

Variables need to be passed to ``report()`` method by their name:

```python
self.report(self.my_rule, variable="some string", number=10, node=node)
```

## Robot Framework version support

You can enable (or disable) your rule for a particular Robot Framework version. Add `version` parameter to the Rule
definition:

```python
class ExampleRule(Rule):
"""
Rule description and documentation.

Supports rst.
"""

name = "external-rule"
rule_id = "EX03"
message = "This is external rule"
severity = RuleSeverity.INFO
version = ">=5.0"
```

In this case rule "external-rule" will be enabled only for Robot Framework versions equal to 5.0 or higher.

It is also possible to adjust the behaviour of your checker depending on the Robot Framework version:

```python title="some_checker.py"
from robocop.linter.utils.misc import ROBOT_VERSION

(...)
if ROBOT_VERSION.major == 3:
    # do stuff for RF 3.x version
else:
    # execute this code for RF != 3.x
```

## File-wide rules

If you want to report a rule violation for a whole file and do not show any specific line in the ``extended`` view, use
``file_wide_rule = True`` attribute in the rule class.

## Change Rule class behaviour

It is possible to change the behaviour or attributes of the Rule class. You can define your own class, which inherits
from ``Rule`` and adjust the code.

For example, if you want to change the rule documentation URL (which is part of some reports),
you can do it in the following way:

```python
from robocop.linter.rules import Rule, RuleSeverity

class CustomParentRule(Rule):
    @property
    def docs_url(self):
        return f"https://your.company.com/robocop/rules/{self.name}"

    
class ExternalRule(CustomParentRule):
    name = "external-rule"
    rule_id = "CUS01"
    message = "Your own rule."
    severity = RuleSeverity.INFO

```

You may override other attributes and methods as well.

## Project checks

Project checkers are special kind of checker that can be only run using ``check-project`` command:

```bash
robocop check-project
```

They are only run once per whole project and accept configuration manager as input to the entrypoint method. It can
be used to run any code, for example, analysis of the project dependencies and architecture.

Example project checker:

```python title="project_checker.py"
from robocop.config import ConfigManager
from robocop.linter.rules import Rule, ProjectChecker, RuleSeverity


class ProjectCheckerRule(Rule):
    rule_id = "PROJ01"
    name = "project-checker-rule"
    message = "This check will be called after visiting all files"
    severity = RuleSeverity.INFO


class TestTotalCountRule(Rule):
    rule_id = "PROJ02"
    name = "test-total-count"
    message = "There is total of {files} files in the project."
    severity = RuleSeverity.INFO


class MyProjectChecker(ProjectChecker):
    """Project checker."""

    project_checker: ProjectCheckerRule
    test_total_count: TestTotalCountRule

    def scan_project(self, config_manager: ConfigManager) -> None:
        files_count = 0
        for robot_file in config_manager.root.rglob("*.robot"):
            files_count += 1
            self.report(self.project_checker, source=robot_file)
        # files can be also parsed (with get_model) and checked here
        self.report(self.test_total_count, source="Project-name", files=files_count)
```

Each project checker must inherit from ``ProjectChecker`` class and implement ``scan_project()`` method.

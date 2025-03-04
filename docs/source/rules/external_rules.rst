.. _external-rules:

Custom rules
=============

You can include your own custom rules with ``--custom-rules`` arguments.
It accepts comma-separated list of paths to files, directories or name of the Python module. Example:

.. tab-set::

    .. tab-item:: Cli

        .. code:: shell

            robocop check --custom-rules my/own/rule.py --custom-rules custom_rules.py

    .. tab-item:: Configuration file

        .. code:: toml

            [robocop.lint]
            custom_rules = [
                "my/own/rule.py",
                "external_rules.py"
            ]

Writing your own rules requires to implement following:

1. Rule class, which describes what code issue we are looking for and how it will be reported
2. Checker class, which scans the code and reports code issues.

Custom rule class inherits from Robocop ``Rule`` class and must override following attributes:

- name (rule name)
- rule_id
- message
- severity
- __doc__ (class documentation that will be used as rule documentation)

It can optionally override following attributes:

- severity_threshold
- version (supported Robot Framework version, for example ``>=6``)
- enabled (default ``True``, can be used to define rules disabled by default)
- deprecated (set to ``True`` to deprecate rule)
- parameters

Example rule definition:

..  code-block:: python
    :caption: rule definition

    from robocop.linter.rules import (
        Rule,
        RuleParam,
        RuleSeverity
    )


    class ArgumentsPerLineRule(Rule):
        """
        Rule description and documentation.

        Supports rst.
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

Such rule can be used by checker class. Checker class can inherit from one of the following:

- ``VisitorChecker`` which visits Robot Framework code using ast
- ``ProjectChecker`` which is called after scanning all the files
- ``RawFileChecker`` which scans every line (without parsing code as Robot Framework code)

Refer to :ref:`rules` for more details.

Each checker class should define which rules it uses as class attribute and rule class as a type. For example:

..  code-block:: python
    :caption: example.py

    from robocop.linter.rules import (
        Rule,
        RuleParam,
        RuleSeverity,
        VisitorChecker
    )


    class ExampleTestCaseRule(Rule):
        """
        Rule description and documentation.

        Supports rst.
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


Rule parameters
---------------

Rules can have configurable values. You need to specify them using RuleParam class and pass it as argument to Rule:

..  code-block:: python
    :caption: example.py

    from robocop.linter.rules import (
        Rule,
        RuleParam,
        RuleSeverity,
        VisitorChecker
    )


    class ExampleTestCaseRule(Rule):
        """
        Rule description and documentation.

        Supports rst.
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
                    variable=configured_param,
                    node=node,
                    col=node.name.find(configured_param))

Configurable parameter can be referred by its ``name`` in command line options:

.. tab-set::

    .. tab-item:: Cli

        .. code:: shell

            robocop check --custom-rules my/own/rule.py --configure example-in-name.param_name=AnotherExample

    .. tab-item:: Configuration file

        .. code:: toml

            [robocop.lint]
            custom_rules = [
                "my/own/rule.py"
            ]
            configure = [
                "example-in-name.param_name=AnotherExample"
            ]

Value of the configurable parameter can be retrieved by using attribute access:

..  code-block:: python

    self.name_of_the_rule.name_of_param

Parameter value is passed as string. Use ``converter`` argument to define a method that will be used to convert the value:

..  code-block:: python

    RuleParam(name="int_param", converter=int, default=10, desc="Optional desc")  # convert str to int
    # my_own_method will be called with custom_param value
    RuleParam(name="custom_param", converter=my_own_method, default="custom", desc="Optional desc")

Templated rule messages
------------------------

When defining rule messages you can use Python string formatting to supply dynamic values to rule message:

..  code-block:: python

    message = "There is '{variable}' in test case name"

Variables need to be passed to ``report()`` method by their name:

..  code-block:: python

    self.report(self.my_rule, variable="some string", number=10, node=node)

Robot Framework version support
--------------------------------
You can enable (or disable) your rule for particular Robot Framework version. Add `version` parameter to Rule definition:

..  code-block:: python

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

In this case rule "external-rule" will be enabled only for Robot Framework versions equal to 5.0 or higher.

To enable rule only for given range of versions, use ``;`` as a delimiter:

..  code-block:: python

    class ExampleRule(Rule):
    """
    Rule description and documentation.

    Supports rst.
    """

    name = "range-5-and-6"
    rule_id = "GOG01"
    message = "Rule that is only enabled for RF version higher than 5 and lower or equal to 6"
    severity = RuleSeverity.INFO
    version = ">5;<=6"

It is also possible to adjust behavior of your checker depending on the Robot Framework version:

..  code-block:: python
    :caption: some_checker.py

    from robocop.utils import ROBOT_VERSION

    (...)
    if ROBOT_VERSION.major == 3:
        # do stuff for RF 3.x version
    else:
        # execute this code for RF != 3.x

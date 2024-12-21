.. _external-rules:

External rules
========================

You can include your own custom rules with ``-rules`` or ``--ext-rules`` arguments.
It accepts comma-separated list of paths to files, directories or name of the Python module. Example::

    robocop -rules my/own/rule.py --ext-rules rules.py,external_rules.py

Every custom checker needs to complete following requirements:

1. It needs to inherit from official checker classes (``VisitorChecker``, ``ProjectChecker`` or ``RawFileChecker``) and
   implement required methods. Refer to :ref:`rules` for more details.

2. There should be a non-empty *rules* dictionary containing rules definition with your checkers.

3. Each checker should contain a tuple *reports* as a class attribute containing names of the rules used by the checker.

4. Using names and rule IDs different than already existing rules is recommended but in case of using the same ones, they will be overwritten.

This is an example of the file with custom checker that asserts that no test have "Example" in the name:

..  code-block:: python
    :caption: example.py

    from robocop.checkers import VisitorChecker
    from robocop.rules import Rule, RuleSeverity

    rules = {
        "9999": Rule(rule_id="9999", name="example-in-name", msg="There is 'Example' in test case name", severity=RuleSeverity.WARNING)
    }


    class NoExamplesChecker(VisitorChecker):
        reports = ("example-in-name",)

        def visit_TestCaseName(self, node):  # noqa: N802
            if 'Example' in node.name:
                self.report("example-in-name", node=node, col=node.name.find('Example'))

Rule parameters
---------------
Rules can have configurable values. You need to specify them using RuleParam class and pass it as argument to Rule:

..  code-block:: python
    :caption: example.py

    from robocop.checkers import VisitorChecker
    from robocop.rules import Rule, RuleParam, RuleSeverity


    rules = {
        "9999": Rule(
            RuleParam(name="param_name", converter=str, default="Example", desc="Optional desc"),
            rule_id="9999",
            name="example-in-name",
            msg="There is '{% raw %}{{ variable }}{% endraw %}' in test case name",
            severity=RuleSeverity.WARNING,
        )
    }


    class NoExamplesChecker(VisitorChecker):
        reports = ("example-in-name",)

        def visit_TestCaseName(self, node):  # noqa: N802
            configured_param = self.param("example-in-name", "param_name")
            if configured_param in node.name:
                self.report(
                    "example-in-name",
                    variable=configured_param,
                    node=node,
                    col=node.name.find(configured_param))

Configurable parameter can be referred by its ``name`` in command line options::

    robocop --ext-rules my/own/rule.py --configure example-in-name:param_name:AnotherExample

Value of the configurable parameter can be retrieved using ``param`` method:

..  code-block:: python

    self.param("name-of-the-rule", "name-of-param")

Parameter value is passed as string. Use ``converter`` argument to define a method that will be used to convert the value:

..  code-block:: python

    RuleParam(name="int_param", converter=int, default=10, desc="Optional desc")  # convert str to int
    # my_own_method will be called with custom_param value
    RuleParam(name="custom_param", converter=my_own_method, default="custom", desc="Optional desc")

Templated rule messages
------------------------
When defining rule messages you can use ``jinja`` templates. The most basic usage is supplying variables to rule message:

..  code-block:: python

    rules = {
        "9001": Rule(
            rule_id="9001",
            name="my-rule",
            msg="You can supply variables like {% raw %}{{ variable }} or {{ number }}{% endraw %}. "
                "Basic {% if number==10 %}jinja {% endif %}syntax supported",
            severity=RuleSeverity.ERROR
        )
    }

Variables need to be passed to ``report()`` method by their name:

..  code-block:: python

    self.report("my-rule", variable="some string", number=10, node=node)

Import from external module
----------------------------
Robocop rules can be written in separate, distributed module. For example using ``RobocopRules`` module name and following
directory structure::

    RobocopRules/
    RobocopRules/__init__.py
    RobocopRules/some_rules.py
    setup.py

inside ``__init__.py``:

..  code-block:: python
    :caption: __init__.py

    from .some_rules import CustomRule, rules

You can also import whole files to namespace:

..  code-block:: python
    :caption: __init__.py

    import RobocopRules.some_rules

inside ``some_rules.py``:

..  code-block:: python
    :caption: some_rules.py

    from robocop.checkers import VisitorChecker
    from robocop.rules import Rule, RuleSeverity


    rules = {
        "9903": Rule(rule_id="9903", name="external-rule", msg="This is an external rule", severity=RuleSeverity.INFO)
    }


    class CustomRule(VisitorChecker):
        """ Checker for missing keyword name. """
        reports = ("external-rule",)

        def visit_KeywordCall(self, node):  # noqa: N802
            if node.keyword and 'Example' not in node.keyword:
                self.report("external-rule", node=node)

You can import this rule using module name::

    robocop --ext-rules RobocopRules .

Dotted syntax is also supported::

    robocop --ext-rules RobocopRules.submodule .

``rules`` dictionary should be available at the same level as checker that is using it. It could be either defined
or imported from other files.

Import from rules directory
----------------------------

Robocop rules can discovered from a directory. For example, using the following directory
structure::

    external_rules/
    external_rules/some_rule.py
    external_rules/utilities.py
    setup.py

Inside ``some_rules.py``:

..  code-block:: python
    :caption: some_rules.py

    from robocop.checkers import VisitorChecker
    from robocop.rules import Rule, RuleSeverity
    from external_rules.utilities import DISALLOWED_KEYWORDS


    rules = {
        "9903": Rule(rule_id="9903", name="external-rule", msg="This is an external rule", severity=RuleSeverity.INFO)
    }


    class CustomRule(VisitorChecker):
        """ Checker for missing keyword name. """
        reports = ("external-rule",)

        def visit_KeywordCall(self, node):  # noqa: N802
            if node.keyword and node.keyword not in DISALLOWED_KEYWORDS:
                self.report("external-rule", node=node)

Inside ``utilities.py``:

..  code-block:: python
    :caption: utilities.py

    DISALLOWED_KEYWORDS = ['Some Keyword', 'Another Keyword']

Note how you can import other files from the directory:

..  code-block:: python

    from external_rules.utilities import DISALLOWED_KEYWORDS

You can also import relative to the external rules directory:

..  code-block:: python

    from utilities import DISALLOWED_KEYWORDS

You can import this rule directory using a relative path to the directory::

    robocop --ext-rules ./external_rules .

Rules disabled by default
-------------------------

All rules are enabled by default and included after importing them. It is possible to define a rule that is disabled
by using ``enabled`` parameter with ``False`` value::

    rules = {
        "1155": Rule(
            rule_id="1155",
            name="custom-rule",
            msg="Custom rule message",
            severity=RuleSeverity.INFO,
            enabled=False,
            docs="""
            Custom rule description.
            """,
        )
    }

Such rules can be enabled when called explicitly with ``--include`` option::

    robocop --include custom-rule .

or by configuring ``enabled`` parameter directly::

    robocop --ext-rules custom_rules.py -c custom-rule:enabled:True .

Robot Framework version support
--------------------------------
You can enable (or disable) your rule for particular Robot Framework version. Add `version` parameter to Rule definition::

    rules = {
        "9903": Rule(rule_id="9903", name="external-rule", msg="This is external rule", severity=RuleSeverity.INFO, version=">=5.0")
    }

In this case rule "external-rule" will be enabled only for Robot Framework versions equal to 5.0 or higher.

To enable rule only for given range of versions, use ``;`` as a delimiter::

    rules = {
        "1105": Rule(
            rule_id="1105",
            name="range-5-and-6",
            msg="Rule that is only enabled for RF version higher than 5 and lower or equal to 6",
            severity=RuleSeverity.INFO,
            version=">5;<=6",
        ),
    }

It is also possible to adjust behavior of your checker depending on the Robot Framework version:

..  code-block:: python
    :caption: some_checker.py

    from robocop.utils import ROBOT_VERSION

    (...)
    if ROBOT_VERSION.major == 3:
        # do stuff for RF 3.x version
    else:
        # execute this code for RF != 3.x

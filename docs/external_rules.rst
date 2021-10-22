.. _external-rules:

External rules
========================

You can include your own custom rules with ``-rules`` or ``--ext-rules`` arguments.
It accepts comma separated list of paths to files or directories. Example::

    robocop -rules my/own/rule.py --ext-rules rules.py,external_rules.py

Every custom checker needs to complete following requirements:

1. It needs to inherit from official checker classes (``VisitorChecker`` or ``RawFileChecker``) and implement required methods. Refer to :ref:`rules` for more details.

2. There should be non-empty *rules* dictionary containing rules definition in the file with your checkers.

3. Each checker should contain *reports* tuple class attribute containing names of the rules used by the checker.

3. It can reuse rule ids or names from official rules but it will overwrite them.

This is an example of the file with custom checker that asserts that no test have "Dummy" in the name::

    from robocop.checkers import VisitorChecker
    from robocop.rules import Rule

    rules = {
        "9999": Rule(rule_id="9999", name="dummy-in-name", msg="There is 'Dummy' in test case name", severity="W")
    }


    class NoDummiesChecker(VisitorChecker):
        reports = ("dummy-in-name",)

        def visit_TestCaseName(self, node):
            if 'Dummy' in node.name:
                self.report("dummy-in-name", node=node, col=node.name.find('Dummy'))

Rules can have configurable values. You need to specify them using RuleParam class and pass it as not named arg to Rule::

    from robocop.checkers import VisitorChecker
    from robocop.rules import Rule, RuleParam


    rules = {
        "9999": Rule(
            RuleParam(name="param_name", converter=str, default="Dummy", desc="Optional desc"),
            rule_id="9999",
            name="dummy-in-name",
            msg="There is '%s' in test case name",
            severity="W"
        )
    }


    class NoDummiesChecker(VisitorChecker):
        reports = ("dummy-in-name",)

        def visit_TestCaseName(self, node):
            if self.private_name in node.name:
                self.report(
                    "dummy-in-name",
                    self.param("dummy-in-name", "param_name"),
                    node=node,
                    col=node.name.find(self.param("dummy-in-name", "param_name")))

Configurable parameter can be referred by its :code:`param_name` in command line options::

    robocop --ext-rules my/own/rule.py --configure dummy-in-name:param_name:AnotherDummy

Value of the configurable parameter can be retrieved using :code:`param` method::

    self.param("name-of-the-rule", "name-of-param")

Import from external module
----------------------------
Robocop rules can be written in separate, distributed module. For example using ``RobocopRules`` module name and following
directory structure::

    RobocopRules/
    RobocopRules/__init__.py
    RobocopRules/some_rules.py
    setup.py

inside ``__init__.py``::

    from .some_rules import CustomRule, rules

inside ``some_rules.py``::

    from robocop.checkers import VisitorChecker
    from robocop.rules import Rule


    rules = {
        "9903": Rule(rule_id="9903", name="external-rule", msg="This is external rule", severity="I")
    }


    class CustomRule(VisitorChecker):
        """ Checker for missing keyword name. """
        reports = ("external-rule",)

        def visit_KeywordCall(self, node):  # noqa
            if node.keyword and 'Dummy' not in node.keyword:
                self.report("external-rule", node=node)

You can import is using module name::

    robocop --ext-rules RobocopRules .

Dotted syntax is also supported::

    robocop --ext-rules RobocopRules.submodule .

:code:`rules` dictionary should be available at the same level as checker that is using it. That's why if you are defining your
external rules using modules and `__init__.py` it should be also imported (or defined directly in `__init__.py`).

You can enable (or disable) your rule for particular Robot Framework version. Add `version` parameter to Rule definition::

    rules = {
        "9903": Rule(rule_id="9903", name="external-rule", msg="This is external rule", severity="I", version=">=5.0")
    }

In this case rule "external-rule" will be disabled for all Robot Framework versions except 5.0 and newer.

It is also possible to adjust behaviour of your checker depending on the Robot Framework version::

    from robocop.utils import ROBOT_VERSION

    (...)
    if ROBOT_VERSION.major == 3:
        # do stuff for RF 3.x version
    else:
        # execute this code for RF != 3.x

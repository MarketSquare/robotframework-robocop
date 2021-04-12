.. _external-rules:

External rules
========================

You can include your own custom rules with ``-rules`` or ``--ext-rules`` arguments.
It accepts comma separated list of paths to files or directories. Example::

    robocop -rules my/own/rule.py --ext-rules rules.py,external_rules.py

Every custom checker needs to complete following requirements:

1. It needs to inherit from official checker classes (``VisitorChecker`` or ``RawFileChecker``) and implements required methods. Refer to :ref:`rules` for more details.

2. It should contain non-empty *rules* class attribute of type ``dict``.

3. It should not reuse rules ids or names from official rules.

This is an example of a file with custom checker that asserts that no test have "Dummy" in the name::

    from robocop.checkers import VisitorChecker
    from robocop.rules import RuleSeverity


    class NoDummiesChecker(VisitorChecker):
        rules = {
            "9999": (
                "dummy-in-name",
                "There is 'Dummy' in test case name",
                RuleSeverity.WARNING
            )
        }

        def visit_TestCaseName(self, node):
            if 'Dummy' in node.name:
                self.report("dummy-in-name", node=node, col=node.name.find('Dummy'))

Rules can have configurable values. You need to specify them in rule body after rule severity::

    from robocop.checkers import VisitorChecker
    from robocop.rules import RuleSeverity


    class NoDummiesChecker(VisitorChecker):
        rules = {
            "9999": (
                "dummy-in-name",
                "There is '%s' in test case name",
                RuleSeverity.WARNING,
                ("public_name", "private_name", str)
            )
        }

        def __init__(self, *args):
            self.private_name = "Dummy"
            super().__init__(*args)

        def visit_TestCaseName(self, node):
            if self.private_name in node.name:
                self.report(
                    "dummy-in-name",
                    self.private_name,
                    node=node,
                    col=node.name.find(self.private_name))

Configurable parameter can be referred by its :code:`public_name` in command line options::

    robocop --ext-rules my/own/rule.py --configure dummy-in-name:public_name:AnotherDummy

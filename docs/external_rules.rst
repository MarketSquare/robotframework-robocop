.. _external-rules:

Including external rules
========================

You can include your own custom rules with ``-rules`` or ``--ext_rules`` arguments.
It accepts comma separated list of paths to files or directories. Example::

    robocop -rules my/own/rule.py -rules rules.py,external_rules.py

Every custom checker needs to complete following requirements:

1. It needs to inherit from official checker classes (``VisitorChecker`` or ``RawFileChecker``) and implements required methods.
Refer to :ref:`checkers` for more details.

2. It should contain non-empty *rules* class attribute of type ``dict``.

3. It should not reuse rules ids or names from official rules.

This is an example of a file with custom checker that asserts that no test have "Dummy" in the name::

    from robocop.checkers import VisitorChecker
    from robocop.messages import MessageSeverity


    class NoDummiesChecker(VisitorChecker):
         rules = {
            "9999": (
                "dummy-in-name",
                "There is 'Dummy' in test case name",
                MessageSeverity.WARNING
            )
        }

        def visit_TestCaseName(self, node):
            if 'Dummy' in node.name:
                self.report("dummy-in-name", node=node, col=node.name.find('Dummy'))

Rules can have configurable values. You need to specify them in rule body after rule severity::

    from robocop.checkers import VisitorChecker
    from robocop.messages import MessageSeverity


    class NoDummiesChecker(VisitorChecker):
         rules = {
            "9999": (
                "dummy-in-name",
                "There is 'Dummy' in test case name",
                MessageSeverity.WARNING,
                ("public_name", "private_name", int)
            )
        }

        def __init__(self, *args):
            self.private_name = 100
            super().__init__(*args)

        def visit_TestCaseName(self, node):
            if 'Dummy' in node.name and node.value > self.private_name:
                self.report("dummy-in-name", node=node, col=node.name.find('Dummy'))


Configurable parameter can be referred by its "public_name" in command line options::

    robocop --configure dummy-in-name:public_name:50

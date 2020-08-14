.. _external-rules:

Including external rules
========================

You can include your own custom rules with `-rules` or `--external_rules` arguments. It accepts comma separated list of
paths to files or directories. Example::

    robocop -rules my/own/rule.py -rules rules.py,external_rules.py


Every custom checker (with definied rules) need to complete following requirements:

1. It needs to inherit from official checker classes (VisitorChecker or RawFileChecker) and implements required methods.
Refer to :ref:`checkers` for more details.

2. File with checker should define `register` method where linter is called with instance of your checker::

    def register(linter):
      linter.register_checker(YourChecker(linter))
      linter.register_checker(YourChecker2(linter))
3. It shouldn't reuse messages ids or names from official rules.

This is an example of a file with custom checker that asserts that no test have "Dummy" in the name::

    from robocop.checkers import VisitorChecker
    from robocop.messages import MessageSeverity


    def register(linter):
        linter.register_checker(NoDummiesChecker(linter))


    class NoDummiesChecker(VisitorChecker):
         msgs = {
            "999": (
                "dummy-in-name",
                "There is dummy in test case name",
                MessageSeverity.WARNING
            )
        }

    def visit_TestCaseName(self, node):
        if 'Dummy' in node.name:
            self.report("dummy-in-name", node=node, col=node.name.find('Dummy'))

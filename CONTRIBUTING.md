---- Document under rework -----

Testing
=======

We are using pytest for our test framework. While it would be possible to use Robot Framework, it's easier for us
to use different test framework as we can easily mock in unit tests and setup different robot framework versions
for acceptance testing.

Our tests structure around main features in Robocop:

tests/
    formatter/ - formatting tests
    linter/ - linting tests
    config/ - config related tests (note that some of the config related tests may be still inside linter/formatter)

Typically, users are contributing in following areas:

- adding / updating existing rules
- adding / updating reports
- adding / updating formatters
- core functions changes

We will cover how to approach testing for each category.

Adding / updating existing rules
--------------------------------

After you update or add new rule, or even better before you do it, you need to create tests for it under
``tests/linter/rules/<rule_category>/<rule_name>``. Rule name has replaced ``-` characters with ``_`` so it's
recognized by default by pytest.

For example rule ``invalid_argument`` has tests placed under ``tests/linter/rules/arguments/invalid_argument``
directory.

Each such directory has at least following files: 

- empty ``__init__.py`` file (for tests discovery)
- ``test_rule.py`` file that describes tests
- ``test.robot`` file (name can be different) with Robot Framework code to be linted
- ``expected_output.txt`` with content of output which Robocop is expected to print

Depending on tested features you may have multiple robot files with one expected file, or several expected files
(for example one for every robot version, if rule behaviour change over versions).

Example Python file:

```Python
from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["test.robot"], expected_file="expected_output.txt", test_on_version=">=4"
        )

```

It will select and run only one rule (name will be taken from the directory name) on ``test.robot`` file, compare
output with ``expected_output.txt``. Tests will only run on versions ``>=4``.

Default output format in Robocop is ``extended`` view. Most tests use ``simple`` view by default (for simplicity). 
It's highly recommended to check how rule behaves with both views. You can configure to run on different view
using ``configure``:

```Python
def test_rule(self):
    self.check_rule(
        src_files=["test.robot"], expected_file="expected_output.txt", output_format="extended"
    )
```

Documentation
=============

Robocop uses both dynamically and statically loaded documentation. For documentation backend we are using Sphinx with
furo theme. Documentation source files are stored in ``docs/source``.

After merging the changes, documentation is rebuilt and deployed at https://robocop.readthedocs.io/ . It is however
advised to build documentation locally to check it.

If you are adding or updating new features you may need to update relevant sections in the documentation. For example
if you're changing how external rules works, you may need to update ``docs/source/external_rules.rst`` document.

If you are adding or updating formatter, you need to add or modify file at ``docs/source/formatters/<formatter_name>rst``
(more on this in <> section). # TODO

If you are adding or updating rule, you need to update rule docstring and check how the rule documentation generates
at https://robocop.readthedocs.io/en/stable/rules_list.html . Check <> to see how to add or update existing rules. # TODO

Build documentation locally
----------------------------

If you have Robocop development environment ready (with uv installed), run:

```
    uv run nox -s docs
```

Documentation will build at ``docs/_build``. Open ``docs/_build/index.thml`` to see starting page.

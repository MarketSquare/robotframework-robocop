# CONTRIBUTING

All contributions are welcome.

Contributing may be anything starting from an idea or bug reported in our issues, discussion on our Slack channel
[#robocop-linter](https://robotframework.slack.com/archives/C01AWSNKC2H) located in
[Robot Framework workspace](https://robotframework.slack.com/>) or finally code change directly in the Robocop
repository.

## Submitting issues

Bugs and enhancements are tracked in the [issue tracker](https://github.com/MarketSquare/robotframework-robocop/issues).

Before submitting a new issue, it is always a good idea to check if the
same bug or enhancement is already reported. If it is, please add your comments
to the existing issue instead of creating a new one.

## Code contributions

### Development environment

To set up your local development environment, use install uv first:

```commandline
pip install uv
```

You can now run our tests with:

```commandline
uv run pytest tests
```

``uv``` will create a local environment for you. You can use it in your IDE for type hinting or to run selected tests
from the UI.

To test Robocop on multiple Python and Robot versions, you need to create multiple environments and run tests
through nox. You will need nox:

```commandline
pip install nox
```

And multiple Python versions:

```commandline
uv python install 3.9 3.10 3.11 3.12 3.13
```

To run all nox sessions (defined in ``noxfile.py``), run in the root of the project:

```commandline
nox -s tests
```

Running all combinations may take a while. Instead, you can run all major supported Robot versions using
a selected Python version with:

```commandline
nox -s --python 3.13 tests
```

## Coding conventions

Robocop uses ruff as a basic tool for formatting and linting code. Run it using pre-commit to ensure that
every commit follows our code conventions:

```commandline
pip install pre-commit
```

Run from the root of the project:

```commandline
pre-commit install
```

## Testing

We are using pytest for our test framework. While it would be possible to use Robot Framework, it's easier for us
to use a different test framework as we can easily mock in unit tests and set up different robot framework versions
for acceptance testing.

Our tests structure around main features in Robocop:

```text
tests/
    formatter/ - formatting tests
    linter/ - linting tests
    config/ - config related tests (note that some of the config related tests may be still inside linter/formatter)
    migrate_config/ - tests for robocop migrate command
```

Typically, users are contributing in the following areas:

- adding / updating existing rules
- adding / updating reports
- adding / updating formatters
- core functions changes

We will cover how to approach testing for each category.

## Adding / updating existing rules

After you update or add new rule, or even better before you do it, you need to create tests for it under
``tests/linter/rules/<rule_category>/<rule_name>``. Rule name has replaced ``-`` characters with ``_`` so it's
recognised by default by pytest.

For example, rule ``invalid-argument`` has tests placed under ``tests/linter/rules/arguments/invalid_argument``
directory.

Each such directory has at least the following files:

- empty ``__init__.py`` file (for tests discovery)
- ``test_rule.py`` file that describes tests
- ``test.robot`` file (name can be different) with Robot Framework code to be linted
- ``expected_output.txt`` with content of output which Robocop is expected to print

Depending on tested features, you may have multiple robot files with one expected file, or several expected files
(for example, one for every robot version, if rule behaviour changes over versions).

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
It's highly recommended to check how the rule behaves with both views. You can configure to run on different view
using ``configure``:

```Python
def test_rule(self):
    self.check_rule(
        src_files=["test.robot"], expected_file="expected_output.txt", output_format="extended"
    )
```

## Documentation

Robocop uses both dynamically and statically loaded documentation.

For documentation backend we are using mkdocs with the material theme. Documentation source files are stored in ``docs``.

After merging the changes, documentation is rebuilt and deployed at [https://robocop.dev/](https://robocop.dev/). It is advised to build
documentation locally to check it.

If you are adding or updating new features, you may need to update relevant sections in the documentation. For example,
if you're changing how external rules works, you may need to update ``docs/linter/custom_rules.md`` document.

If you are adding or updating formatter, you need to add or modify a file at ``docs/formatter/formatters/<formatter_name>.md``.

If you are adding or updating a rule, you need to update the rule docstring and check how the rule documentation
generates at [https://robocop.dev/stable/rules_list/](https://robocop.dev/stable/rules_list/).

### Build documentation locally

If you have a Robocop development environment ready (with uv installed), run:

```bash
uv run mkdocs serve
```

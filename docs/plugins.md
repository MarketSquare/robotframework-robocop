# Plugins

Robocop plugins allow you to package and distribute custom rules, formatters and configuration files as a regular
Python package. Once the plugin package is installed, its resources can be referenced in the Robocop configuration
using a short, namespaced syntax instead of file paths.

## Using a plugin

Install the plugin package the same way as any other Python package:

```bash
pip install example-plugin
```

Robocop discovers installed plugins automatically. You can list them with:

```bash
robocop list plugins
```

Installing a plugin does **not** enable anything on its own. It only registers the plugin namespace, so its
resources can be referenced in the configuration.

### Rules

Point ``custom-rules`` to a module inside the plugin:

=== ":octicons-command-palette-24: cli"

    ```
    robocop check --custom-rules example.rules --select plugin-rule
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    custom_rules = [
        "example.rules"
    ]
    select = [
        "plugin-rule"
    ]
    ```

All submodules of the referenced module are imported, so the plugin does not have to import them in its
``__init__.py``.

### Formatters

Select a single formatter class or a whole module with formatters:

=== ":octicons-command-palette-24: cli"

    ```
    robocop format --select example.formatters.ExampleFormatter
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "example.formatters.ExampleFormatter",
    ]
    ```

Formatters are configured by their class name, without the plugin namespace:

```toml
[tool.robocop.format]
configure = [
    "ExampleFormatter.test_name=Configured Name"
]
```

### Reports

Enable reports shipped with a plugin by pointing ``reports`` to a module with the reports:

=== ":octicons-command-palette-24: cli"

    ```
    robocop check --reports example.reports
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "example.reports"
    ]
    ```

All reports from the referenced module are loaded and enabled. Use the full reference
(``example.reports.issues_count``) to only enable reports from the selected module. Reports are configured by their
name, without the plugin namespace:

```toml
[tool.robocop.lint]
configure = [
    "issues_count.prefix=Issues"
]
```

### Configuration files

Configuration files shipped with a plugin are used with the [extends](configuration/index.md#inherit-configuration-file)
option:

```toml
[tool.robocop]
extends = ["example.config.strict"]
```

The reference points to the ``config/strict.toml`` file inside the plugin. Such a configuration file can itself
reference other plugin resources:

```toml title="config/strict.toml"
[tool.robocop.lint]
custom_rules = [
    "example.rules"
]
select = [
    "plugin-rule"
]

[tool.robocop.format]
select = [
    "example.formatters.ExampleFormatter"
]
```

## Creating a plugin

A plugin is a Python package that registers itself using the ``robocop.plugins``
[entry point group](https://packaging.python.org/en/latest/specifications/entry-points/):

```toml title="pyproject.toml"
[project]
name = "example-plugin"
version = "1.0.0"

[project.entry-points."robocop.plugins"]
example = "example_plugin"
```

The entry point name (``example``) is the plugin namespace used in the Robocop configuration. The value is an
importable path to the Python package with the plugin resources. It does not have to be the top level package:

```toml
[project.entry-points."robocop.plugins"]
example = "example_plugin.path.to.dir"
```

### Reference syntax

Every plugin resource is referenced with the ``<plugin_name>.<path.inside.the.plugin>`` syntax. The first part is
always the plugin name, and the rest is a dot separated path relative to the package the entry point points to.
Robocop does not enforce any particular directory layout, but the following one is a good starting point:

```
example_plugin/
    __init__.py
    rules/
        __init__.py
        naming.py
    formatters/
        __init__.py
        ExampleFormatter.py
    reports/
        __init__.py
        issues_count.py
    config/
        strict.toml
```

With such a layout, the plugin provides:

| Reference | Resolved to |
| --- | --- |
| ``example.rules`` | ``example_plugin/rules`` package with the rules and checkers |
| ``example.formatters`` | all formatters from the ``example_plugin/formatters`` package |
| ``example.formatters.ExampleFormatter`` | single ``ExampleFormatter`` formatter |
| ``example.reports`` | all reports from the ``example_plugin/reports`` package |
| ``example.config.strict`` | ``example_plugin/config/strict.toml`` configuration file |

!!! note

    Plugin names take precedence over file paths and module names. If a plugin called ``example`` is installed,
    ``example.rules`` is always resolved as a plugin reference.

### Rules

Rules and checkers inside a plugin are written exactly the same way as any other
[custom rule](linter/custom_rules.md):

```python title="example_plugin/rules/naming.py"
from robocop.linter.rules import Rule, RuleSeverity, VisitorChecker


class PluginRule(Rule):
    """Rule shipped with the example plugin."""

    name = "plugin-rule"
    rule_id = "EXPL01"
    message = "Test case name '{name}' comes from the plugin rule"
    severity = RuleSeverity.INFO
    added_in_version = "1.0.0"


class PluginChecker(VisitorChecker):
    plugin_rule: PluginRule

    def visit_TestCaseName(self, node):  # noqa: N802
        self.report(self.plugin_rule, name=node.name, node=node)
```

### Formatters

Formatters follow the [custom formatter](formatter/formatter.md) rules - the file name must match the formatter
class name:

```python title="example_plugin/formatters/ExampleFormatter.py"
from robot.api.parsing import Token

from robocop.formatter.formatters import Formatter


class ExampleFormatter(Formatter):
    """Formatter shipped with the example plugin."""

    ENABLED = False

    def __init__(self, test_name: str = "Plugin Test"):
        super().__init__()
        self.test_name = test_name

    def visit_TestCaseName(self, node):  # noqa: N802
        name_token = node.get_token(Token.TESTCASE_NAME)
        if name_token is not None:
            name_token.value = self.test_name
        return node
```

Use the ``FORMATTERS`` list in the ``__init__.py`` of the formatters package to define the order in which the
formatters are run when the whole module is selected:

```python title="example_plugin/formatters/__init__.py"
from example_plugin.formatters.ExampleFormatter import ExampleFormatter

FORMATTERS = ["ExampleFormatter"]
```

### Reports

Reports inside a plugin follow the [custom report](linter/reports/reports.md#custom-reports) rules:

```python title="example_plugin/reports/issues_count.py"
from robocop.linter.reports import Report


class IssuesCountReport(Report):
    """Report shipped with the example plugin."""

    def __init__(self, config):
        self.name = "issues_count"
        self.description = "Returns number of found issues"
        super().__init__(config)

    def generate_report(self, diagnostics, **kwargs):
        print(f"Found {len(diagnostics.diagnostics)} issues")
```

### Configuration files

Configuration files shipped with the plugin use the same syntax as any other Robocop configuration file and
require the ``[tool.robocop]`` section.
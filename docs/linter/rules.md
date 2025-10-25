# Rules

Robocop uses rules as a basic building block of the linter. They can define what message will be printed in the report,
which Robot Framework versions it supports or provide additional configuration for the rule. Rules are internally
used by checkers, which are classes that scan code for related issues and report them as Diagnostic issues.

Each rule has a unique rule id (for example ``DOC01``) consisting of:

- an alphanumeric group name (for example ``DOC``)
- a 2-digit rule number (for example ``01``)

Rule ID as well as rule name can be used to refer to the rule (e.g. in select/ignore statements, configurations, etc.).
You can optionally configure rule severity or other parameters.

## List available rules

To get a list of available rules (with enabled/disabled status) use ``list rules`` command:

```bash
> robocop list rules
Rule - ARG01 [W]: unused-argument: Keyword argument '{name}' is not used (enabled)
Rule - ARG02 [W]: argument-overwritten-before-usage: Keyword argument '{name}' is overwritten before usage (enabled)
Rule - ARG03 [E]: undefined-argument-default: Undefined argument default, use {arg_name}=${{EMPTY}} instead (enabled)
(...)
```

Rules list can be filtered out by a glob pattern:

```bash
> robocop list rules --pattern tag*
Rule - TAG01 [W]: tag-with-space: Tag '{tag}' contains spaces (enabled)
Rule - TAG02 [I]: tag-with-or-and: Tag '{tag}' with reserved word OR/AND (enabled)
Rule - TAG03 [W]: tag-with-reserved-word: Tag '{tag}' prefixed with reserved word `robot:` (enabled)
Rule - TAG06 [I]: tag-already-set-in-test-tags: Tag '{tag}' is already set by {test_force_tags} in suite settings (enabled)
Rule - TAG11 [I]: tag-already-set-in-keyword-tags: Tag '{tag}' is already set by {keyword_tags} in suite settings (enabled)
```

To list only enabled or disabled rules:

```bash
> robocop list rules --pattern tag-with* --filter ENABLED
Rule - TAG01 [W]: tag-with-space: Tag '{tag}' contains spaces (enabled)
Rule - TAG02 [I]: tag-with-or-and: Tag '{tag}' with reserved word OR/AND (enabled)
Rule - TAG03 [W]: tag-with-reserved-word: Tag '{tag}' prefixed with reserved word `robot:` (enabled)

> robocop list rules --pattern non-builtin-imports-not-sorted --filter DISABLED
Rule - IMP03 [W]: non-builtin-imports-not-sorted: Non builtin library import '{custom_import}' should be placed before '{previous_custom_import}' (disabled)
```

Available list filters:

```text
DEFAULT - no pattern specified, print all default rules (enabled and disabled)
ENABLED - print only enabled rules
DISABLED - print only disabled rules
DEPRECATED - print only deprecated rules
STYLE_GUIDE - print only rules directly connected to official Robot Framework style guide
```

## Rule severity
-------------

Robocop rules can have one of the following severities: ``info``, ``warning`` or ``error``.

You can override the rule default severity:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --configure id_or_msg_name.severity=value
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    configure = [
        "id_or_msg_name.severity=value"
    ]
    ```

where value can be the first letter of severity value or whole name, case-insensitive.

For example, to change ``line-too-long`` rule severity to error:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check -c line-too-long.severity=e
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    configure = [
        "line-too-long.severity=e"
    ]
    ```

You can filter out all rules below given severity value by using ``-t/--threshold`` option:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check -t <severity value>
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    threshold = "<severity value>"
    ```

To only report rules with severity W and above:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check -t W
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    threshold = "W"
    ```

## Severity threshold

Selected rules can be configured to have different severity depending on the parameter value.

Using ``line-too-long`` as an example - this rule issues a warning when line length exceeds configured value
(default ``120``).
It is possible to configure this rule to issue a warning for line length above 120 but an error for line length
above 200.
We can use ``severity_threshold`` for this purpose:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check -c line-too-long.severity_threshold=warning=120:error=200
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    configure = [
        "line-too-long.severity_threshold=warning=120:error=200"
    ]
    ```

It supports all default severity values:

- error, e
- warning, w
- info, i

The issue needs to be raised in order for severity thresholds to be evaluated. That's why the parameter value needs to
be configured to raise an issue for at least one of our threshold ranges. In previous example, if we want to issue
an info message if the line is longer than 80 characters, we need to configure ``line_length`` parameter
(default ``120``) to 80 to trigger the rule:

=== ":octicons-command-palette-24: cli"

    ```
    robocop check -c line-too-long.line_length=80 -c line-too-long.severity_threshold=info=80:warning=120:error=200
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    configure = [
        "line-too-long.line_length=80",
        "line-too-long.severity_threshold=info=80:warning=120:error=200"
    ]
    ```

Rules list page contains information which rules support severity thresholds.

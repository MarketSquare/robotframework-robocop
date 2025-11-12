# Rules by ID

Report name: **rules_by_id**

Available in ``all``: Yes

Comparable report: Yes ([Comparing results](reports.md#comparing-results))

Report that groups linter rule messages by rule id and print it ordered by the most common message.

Example:

```text
Issues by ID:
VAR03  [W] (variable-overwritten-before-usage) : 5
DOC01  [W] (missing-doc-keyword)               : 4
ERR01  [E] (parsing-error)                     : 3
NAME01 [W] (not-allowed-char-in-name)          : 2
MISC01 [W] (keyword-after-return)              : 1
```

Enable with:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports rules_by_id
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "rules_by_id"
    ]
    ```

You can also enable it by using ``all``  which enables all reports that supports ``all`` option:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports all
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "all"
    ]
    ```

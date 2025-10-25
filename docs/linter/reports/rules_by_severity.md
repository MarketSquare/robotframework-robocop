# Rules by severity

Report name: **rules_by_error_type**

Available in ``all``: Yes

Comparable report: Yes ([Comparing results](reports.md#comparing-results))

Report that groups linter rules messages by severity and prints a total number of issues per every severity level.

Example:

```text
Found 15 issues: 4 ERRORs, 11 WARNINGs.
```

Enable with:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports rules_by_error_type
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "rules_by_error_type"
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

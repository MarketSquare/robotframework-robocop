# Time taken

Report name: **scan_timer**

Available in ``all``: Yes

Comparable report: Yes ([Comparing results](reports.md#comparing-results))

Report that prints Robocop execution time.

Example:

```text
Scan finished in 0.054s.
```

Enable with:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports scan_timer
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "scan_timer"
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

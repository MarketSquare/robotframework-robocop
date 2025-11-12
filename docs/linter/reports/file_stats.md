# File statistic

Report name: **file_stats**

Available in ``all``: Yes

Comparable report: Yes ([Comparing results](reports.md#comparing-results))

Report that displays overall statistics about the number of processed files.

Example:

```text
Processed 7 files from which 5 files contained issues.
```

Enable with:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports file_stats
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "file_stats"
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

# JSON

Report name: **json_report**

Report that exports found issues to file in a JSON format.

Enable with:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports json_report
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "json_report"
    ]
    ```

Example content of the file:

```json
[
    {
        "source": "C:\robot_tests\keywords.robot",
        "line": 1,
        "end_line": 1,
        "column": 1,
        "end_column": 1,
        "severity": "I",
        "rule_id": "0913",
        "description": "No tests in 'keywords.robot' file, consider renaming to 'keywords.resource'",
        "rule_name": "can-be-resource-file"
    },
    {
        "source": "C:\\robot_tests\\keywords.robot",
        "line": 51,
        "end_line": 51,
        "column": 1,
        "end_column": 13,
        "severity": "W",
        "rule_id": "0324",
        "description": "Variable '${TEST_NAME}' overwrites reserved variable '${TEST_NAME}'",
        "rule_name": "overwriting-reserved-variable"
    }
]
```

## Configuration

### ``Output path``

You can configure an output path with the ``output_path`` option. It's a relative path to the file that will be produced
by the report:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports json --configure json_report.output_path=C:/json_reports/report.json
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "json"
    ]
    configure = [
        "json_report.output_path=C:/json_reports/report.json"
    ]
    ```

The default path is ``robocop.json``.

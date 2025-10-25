# Reports

Reports are configurable summaries after a Robocop scan. For example, it can display the total number of issues
discovered.

Report class collects diagnostic messages from a linter and can optionally parse them. At the end of the scan it will
generate the report.

To enable report use ``-r`` / ``--reports`` option and provide the name of the report.
You can use multiple reports with separate arguments (``-r report1 -r report2``) or comma-separated list
(``-r report1,report2``). For example:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports rules_by_id,some_other_report
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "rules_by_id",
        "some_other_report"
    ]
    ```

???+ note

    Reports can be only enabled and configured from the configuration file closest to the current working directory.
    If you configure reports in multiple configuration files, only one configuration file will apply.

To enable all default reports use ``--reports all``.  Non-default reports can be only enabled using their name.

The order of the reports is preserved. For example, if you want ``timestamp`` report to be printed before any
other reports, you can use the following configuration:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports timestamp,all
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "timestamp",
        "all"
    ]
    ```
## List available reports

Print a list of all reports with their configured status by using ``list reports`` command:

```bash
robocop list reports
```

Configuration is reflected in the output:

```bash
robocop list reports --reports all
```

will print:

```text
Available reports:
file_stats           - Prints overall statistics about number of processed files (enabled)
gitlab               - Generate Gitlab Code Quality output file (disabled - not included in all)
json_report          - Produces JSON file with found issues (disabled - not included in all)
print_issues         - Collect and print rules messages (enabled - not included in all)
return_status        - Checks if number of specific issues exceed quality gate limits (disabled - not included in all)
rules_by_error_type  - Prints total number of issues grouped by severity (enabled)
rules_by_id          - Groups detected issues by rule id and prints it ordered by most common (enabled)
sarif                - Generate SARIF output file (disabled - not included in all)
scan_timer           - Returns Robocop execution time (enabled)
sonarqube            - Generate SonarQube report (disabled - not included in all)
text_file            - Print rules messages to the file (disabled - not included in all)
timestamp            - Returns Robocop execution timestamp. (enabled)
version              - Returns Robocop version (enabled)

Enable report by passing report name using --reports option. Use `all` to enable all default reports. Non-default reports can be only enabled using report name.
```

You can filter the list using ``--enabled`` / ``--disabled`` flags:

```bash
robocop list reports --disabled
```

## Comparing results

Several reports allow comparing the current run with the previous run. ``--persistent`` and ``--compare`` options can
be used to display a comparison report.

Example output:

```text
Found 18 (-3) issues: 13 (-4) INFOs, 5 (+1) WARNINGs.

Issues by ID:
MISC12 [I] (unnecessary-string-conversion)    : 10 (+0)
NAME01 [W] (not-allowed-char-in-name)         : 2 (+0)
VAR02 [I] (unused-variable)                   : 2 (-4)
VAR03 [W] (variable-overwritten-before-usage) : 2 (+1)
TAG05 [I] (could-be-test-tags)                : 1 (+0)
VAR11 [W] (overwriting-reserved-variable)     : 1 (+0)
```

You can enable this feature by using first storing current run with ``--persistent`` flag:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports all --persistent
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    persistent = true
    reports = [
        "all"
    ]
    ```

???+ note

    You can use specific reports instead of ``all`` to compare only selected reports.

Robocop stores a previous result in the cache directory.

Cache directory is stored in the different location depending on the platform:

- Linux: ``"~/.cache/robocop"``
- macOS: ``"~/Library/Caches/robocop"``
- Windows: ``"C:\\Users\\<username>\\AppData\\Local\\robocop"``

Only the previous run for the current working directory is saved.

Now use ``--compare`` flag to enhance reports with the previous run comparison:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports all --compare
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    compare = true
    reports = [
        "all"
    ]
    ```

Combine both flags to always store the current run and display the difference with the previous one.

## Disable all reports

When handling multiple configuration sources, it may be possible to inherit reports configuration that we don't want to
use. Use special keyword ``None`` to not run any reports even if configured:

```bash
robocop check --reports sarif,all,None
```

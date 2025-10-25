# Print Issues

Report name: **print_issues**

Report that collect diagnostic messages and print them at the end of the execution.

It is a default, always enabled report.

## Configuration

### ``Output format``

Use ``output_format`` parameter to configure an output format. Supported output types are:

- **extended** (default), which print issue together with source code:

    ```bash
    test.robot:2:14 DEPR02 'Run Keyword If' is deprecated since Robot Framework version 5.*, use 'IF' instead
       |
     1 | *** Settings ***
     2 | Suite Setup  Run Keyword If
       |              ^^^^^^^^^^^^^^ DEPR02
     3 | Suite Teardown  Run Keyword If
     4 | Force Tags         tag
       |
    
    ```
    
- **grouped**, which prints issues grouped by source files:

    ```bash
    templated_suite.robot:
      1:1 MISC06 No tests in 'templated_suite.robot' file, consider renaming to 'templated_suite.resource' (can-be-resource-file)
      2:18 DEPR02 'Run Keyword Unless' is deprecated since Robot Framework version 5.*, use 'IF' instead (deprecated-statement)

    test.robot:
      1:1 DOC03 Missing documentation in suite (missing-doc-suite)
      3:17 DEPR02 'Run Keyword If' is deprecated since Robot Framework version 5.*, use 'IF' instead (deprecated-statement)

    ```

- **simple**, which print issue in one line. It also allows configuring the format of a message:

    ```bash
    variable_errors.robot:7:1 [E] ERR01 Robot Framework syntax error: Invalid dictionary variable item '1'. Items must use 'name=value' syntax or be dictionary variables themselves.
    positional_args.robot:3:32 [E] ERR01 Robot Framework syntax error: Positional argument '${arg2}' follows named argument
    ```

Configuration example:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --configure print_issues.output_format=grouped
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    configure = [
        "print_issues.output_format=grouped"
    ]
    ```

Format of the **simple** output type can be configured with the global ``--issue-format`` option:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --issue-format "{source}:{line}:{col} [{severity}] {rule_id} {desc} ({name})"
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    issue-format = "{source}:{line}:{col} [{severity}] {rule_id} {desc} ({name})"
    ```

### ``Issue format``

``issue_format`` parameter allows configuring the format of an issue in extended (default) output type:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --configure print_issues.issue_format="{source}"
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    configure = [
        "print_issues.issue_format={source}"
    ]
    ```

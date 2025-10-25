# Return status

Report name: **return_status**

Report that checks if the number of reported issues does not exceed a preset threshold.
If the report is enabled, it will be used as a return status from Robocop.

Enable with:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports return_status
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "return_status"
    ]
    ```

## Configuration

### ``Quality gate``

You can set the threshold for the number of reported issues. By default, it is set to ``{"E": 0, "W": 0, "I": -1}``.
It means that any number of the errors or warnings is not allowed, whereas any number of info messages is allowed.

You can configure the threshold with ``quality_gate`` parameter:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports return_status --configure return_status.quality_gate=e=0:w=10:i=100
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "return_status"
    ]
    configure = [
        "return_status.quality_gate=e=0:w=10:i=100"
    ]
    ```

``e=0:w=10:i=100`` used in the example above means that any number of errors is not allowed, but up to 10 warnings and
100 info messages are allowed before Robocop returns non-zero exit code.

# Text file

Report name: **text_file**

Available in ``all``: No

Report that output issues in the file. Issues format follows ``Print Issues`` simple report format.

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

## Configuration

### ``Output path``

You can configure an output path with the ``output_path`` option. It's a relative path to the file that will be produced
by the report:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports text_file --configure text_file.output_path=output/text_file.txt
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "text_file"
    ]
    configure = [
        "text_file.output_path=output/text_file.txt"
    ]
    ```

The default path is ``robocop.txt``.

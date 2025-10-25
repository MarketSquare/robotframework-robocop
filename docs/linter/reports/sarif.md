# SARIF

Report name: **sarif**

Available in ``all``: No

Report that generates SARIF output file.

SARIF is a JSON-based standard for the representation of results from
static analysis tools. It is supported by different platforms and tools such as GitHub or SonarQube.

Enable with:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports sarif
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "sarif"
    ]
    ```

It will create ``.sarif.json`` file in the current directory.

## Configuration

### ``Output path``

You can configure an output path with the ``output_path`` option. It's a relative path to the file that will be produced
by the report:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports sarif --configure sarif.output_path=output/sarif.json
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "sarif"
    ]
    configure = [
        "sarif.output_path=output/sarif.json"
    ]
    ```

The default path is ``.sarif.json``.

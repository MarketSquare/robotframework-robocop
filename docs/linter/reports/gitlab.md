# Gitlab

Report name: **gitlab**

Report that generates a Gitlab Code Quality output file.

It allows displaying issue information in the Gitlab, for example, in the PR view.
More information at [GitHub Code Quality Report](https://docs.gitlab.com/ci/testing/code_quality/#code-quality-report-format).
Read more about the integration of Robocop with Gitlab [here](../../integrations/gitlab.md).

Enable with:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports gitlab
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "gitlab"
    ]
    ```

It is also possible to use ``--gitlab``  alias:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --gitlab
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    gitlab = true
    ```

It will create ``robocop-code-quality.json`` file in the current directory.

## Configuration

### ``Output path``

You can configure an output path with the ``output_path`` option. It's a relative path to the file that will be produced
by the report:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports gitlab --configure gitlab.output_path=output/robocop_code_quality.json
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "gitlab"
    ]
    configure = [
        "gitlab.output_path=output/robocop_code_quality.json"
    ]
    ```

The default path is ``robocop-code-quality.json``.

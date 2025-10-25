# Jenkins

Robocop is supported by [the Warnings](https://plugins.jenkins.io/warnings-ng) plugin with a Sarif report.

Run Robocop with a Sarif report enabled in a Jenkins pipeline:

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

Sarif report is generated in the current directory under ``<project_name>.sarif.json`` file. # FIXME

Load the results using ``recordIssues`` step:

```text
recordIssues enabledForFailure: true, tool: sarif(pattern: '.sarif.json', name: 'Robocop linter issues')
```

It is also possible to generate other reports and archive them using the archiveArtifacts plugin.

Read more on configuration in the [plugin documentation](https://github.com/jenkinsci/warnings-ng-plugin/blob/main/doc/Documentation.md)

See [SARIF](../linter/reports/sarif.md) for more information about the report and how to configure it.

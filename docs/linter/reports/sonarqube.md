# SonarQube

Report name: **sonarqube**

Available in ``all``: No

Report that generates a Sonarqube generic formatter format output file. Read more about the integration with SonarQube
[here](../../integrations/sonarqube.md).

Enable with:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports sonarqube
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "sonarqube"
    ]
    ```

It will create ``robocop_sonar_qube.json`` file in the current directory.

## Configuration

### ``Output path``

You can configure an output path with the ``output_path`` option. It's a relative path to the file that will be produced
by the report:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports sonarqube --configure sonarqube.output_path=output/sonarqube.json
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "sonarqube"
    ]
    configure = [
        "sonarqube.output_path=output/sonarqube.json"
    ]
    ```

The default path is ``robocop_sonar_qube.json``.

### ``Sonar version``

Robocop supports SonarQube generic formatter formats versions 9.9 and 10.3 (default). Both versions use different
output schemas and are not compatible.

You can configure the version of the SonarQube generic formatter format with the ``sonar_version`` option:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports sonarqube --configure sonarqube.sonar_version=9.9
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "sonarqube"
    ]
    configure = [
        "sonarqube.sonar_version=9.9"
    ]
    ```

# MegaLinter

[MegaLinter](https://megalinter.io/) is a tool that aggregates linters in one tool.

Robocop is already included in MegaLinter in ``all`` and ``cupcake`` flavors. See the
[configuration reference](https://megalinter.io/latest/descriptors/robotframework_robocop/) for more details.

You can customise how Robocop is run by MegaLinter configuration by using variables listed in the configuration
reference. For example, to enforce that your repository configuration file will be used you can set following in the
``.mega-linter.yml`` file:

```yaml
ROBOTFRAMEWORK_ROBOCOP_CONFIG_FILE: pyproject.toml
```

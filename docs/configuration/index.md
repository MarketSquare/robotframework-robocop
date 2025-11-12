# Configuration

Robocop takes its configuration from two sources:

- command line arguments
- configuration file

Most configuration options are available in both sources, but some are only available in the command file (such options
will be marked as such in the documentation).

Run `robocop --help` to see all available options. Each command has its own help message:

```bash
robocop --help
robocop check --help
robocop format --help
... and so on
```

# Configuration file

Robocop supports configuration files in TOML format. Settings from the command line will override settings from the
configuration file.

Robocop uses a configuration file closest to the source, which allows multiple configuration files. However, options
that apply to the entire execution (such as ``--exit-zero`` or report settings) are exclusively read from the top-level
configuration file.

When looking for the configuration file, Robocop searches either for:

- ``pyproject.toml``
- or ``robocop.toml``
- or ``robot.toml``

It will visit parent directories until it finds root of the project determined by existence of ``.git`` directory.
This behaviour can be disabled with ``--ignore-git-dir``.

If you don't want Robocop to find and load configuration files from your project, use ``--ignore-file-config`` flag.

Valid configuration file should contain ``tool.robocop`` section (which can be only omitted for ``robocop.toml`` file)
and options in TOML format.

??? example "Example configuration file"

    ```toml
    [tool.robocop]
    exclude = ["deprecated.robot"]
    include = ["custom.txt"]
    language = ["en", "pl"]

    [tool.robocop.lint]
    select = [
        "rulename",
        "ruleid"
    ]
    ignore = [
        "ruleid"
    ]
    reports = ["all", "sarif"]
    persistent = true
    compare = true
    configure = [
        "line-too-long.line_length=110"
    ]

    [tool.robocop.format]
    select = ["NormalizeNewLines"]
    custom_formatters = ["CustomFormatter.py"]
    configure = [
        "NormalizeNewLines.section_lines=1"
    ]
    diff = true
    line_length = 110
    skip = [
        "documentation"
    ]
    reruns = 3
    ```

You can manually point to location of the config file with the ``--config`` option:

```bash
robocop check --config path/to/config.toml
robocop format --config path/to/config.toml
```

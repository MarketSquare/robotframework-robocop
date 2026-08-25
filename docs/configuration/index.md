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
```

## Configuration file

Robocop supports configuration files in TOML format. Settings from the command line will override settings from the
configuration file.

Robocop uses a configuration file closest to the source, which allows multiple configuration files. However, options
that apply to the entire execution (such as ``--exit-zero`` or report settings) are exclusively read from the top-level
configuration file.

When looking for the configuration file, Robocop searches in the following order:

- ``robocop.toml``
- ``robot.toml``
- ``pyproject.toml``

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
    extend-select = [
        "additional-rule"
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
    extend-select = ["CustomFormatter.py"]
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

## Generate a configuration file

Instead of writing the configuration file from scratch, you can generate one with all the available options using the
``config init`` command:

```bash
robocop config init
```

This creates a ``robocop.toml`` file that documents every global option, linter rule and formatter together with their
default values and a short description. All the options are written as comments, so the generated file reproduces
Robocop's default behaviour until you uncomment and edit the options you want to change.

By default the file is written to ``robocop.toml`` in the current directory. Robocop will not overwrite an existing
file unless you pass ``--force``:

```bash
robocop config init --force
```

Use ``--output`` (``-o``) to write the file to a different location, or ``-`` to print it to the standard output:

```bash
robocop config init --output config/robocop.toml
robocop config init --output -
```

The generated file mirrors the rules and formatters supported by the installed Robot Framework version. Use
``--target-version`` to generate the file for a different Robot Framework version.

## Inherit configuration file

Inherit configuration from another configuration file using ``extends`` option:

```toml
[tool.robocop]
extends = ["../relative/path.toml", "C:/absolute/path.toml"]
```

``extends`` accept both relative and absolute paths. Configuration is loaded in the order they are specified.
List-like options (``select``, ``ignore`` etc.) are merged. String and boolean options are overwritten by the most recent
value.

``extends`` can also point to a configuration file shipped with an installed [plugin](../plugins.md):

```toml
[tool.robocop]
extends = ["example.config.strict"]
```

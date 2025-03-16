.. _configuration:

*************
Configuration
*************

You can configure Robocop using cli or configuration files.

.. rubric:: Command line options

To list Robocop command line options run::

    robocop --help
    robocop check --help
    robocop format --help

.. _config-file:

Configuration file
==================

Robocop supports configuration files in TOML format. Any setting loaded from configuration file will be overwritten
if the same setting is supplied from the command line.

Robocop uses configuration file closest to the source, which allows multiple configuration files. Some options that
affect whole run (like ``--exit-zero`` or reports configuration) is however only loaded from the top level configuration
file.

When looking for configuration file, Robocop search either for:

- ``pyproject.toml``
- or ``robocop.toml``
- or ``robot.toml``

It will visit parent directories until it finds root of the project determined by existence of ``.git`` directory.
This behaviour can be disabled with ``--ignore-git-dir``, which will make Robocop look until it reaches top directory.

Valid configuration file should contain ``tool.robocop`` section (which can be only omitted for ``robocop.toml`` file)
and options in TOML format.

.. dropdown:: Example configuration file

    ::

        [tool.robocop]
        exclude = ["deprecated.robot"]
        include = ["custom.txt"]
        language = ["eng", "pl"]

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
            "NormalizeNewLines.flatten_lines=True"
        ]
        diff = true
        line_length = 110
        skip = [
            "documentation"
        ]
        reruns = 3

You can manually point to location of config file with ``--config``::

    robocop check --config path/to/config.toml
    robocop format --config path/to/config.toml

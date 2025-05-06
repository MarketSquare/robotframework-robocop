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

If you don't want Robocop to find and load configuration files from your project, use ``--ignore-file-config`` flag.

Valid configuration file should contain ``tool.robocop`` section (which can be only omitted for ``robocop.toml`` file)
and options in TOML format.

.. dropdown:: Example configuration file

    ::

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

You can manually point to location of config file with ``--config``::

    robocop check --config path/to/config.toml
    robocop format --config path/to/config.toml


Configuring parameters
======================

If the rule, formatter or report supports configuration via parameters, it can be done using
``--configure name.param=value`` syntax.

For example to configure maximum allowed length of line:

.. tab-set::

    .. tab-item:: Cli

        .. code:: shell

             robocop check --configure line-too-long.line_length=140

    .. tab-item:: Configuration file

        .. code:: toml

            [tool.robocop.lint]
            configure = [
                "line-too-long.line_length=140"
            ]

What is available for configuration is listed in rule, formatter or report documentation.

.. _language_support:

Language support
================

Robot Framework 6.0 added support for Robot settings and headers translation.
Robocop recognizes language markers in the file but needs to be configured if you have translated file without
language marker. You can supply language code or name in the configuration using ``--language`` option::

.. tab-set::

    .. tab-item:: Cli

        .. code:: shell

            robocop check --language pl
            robocop format --language fi

    .. tab-item:: Configuration file

        .. code:: toml

            [tool.robocop]
            language = [
                "pl",
                "fi"
            ]

Language header in the file is supported by default::

    language: pl

    *** Zmienne ***
    ${VAR}   1

Custom language file is currently not supported.

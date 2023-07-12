.. _configuration file:

*************
Configuration
*************

Robocop provides a wide set of rules with good defaults and is designed to work well out-of-the-box.
Nevertheless, it is natural that some projects may have different needs and requirements, which influence the way the code is written.
Thus, Robocop allows to configure many rules to fit these needs.
It's done using CLI options and such configuration can be stored and loaded from file, as described below.

Configuring rules
=================

Rules are configurable. Severity of every rule message can be changed (see more :ref:`severity-threshold`) and also some of the rules have
optional parameters.

.. note::

    To see all configurable rules and their parameters, run ``robocop --list-configurables`` or just ``robocop -lc``.

For configuring rules you can use ``--configure`` or ``-c`` option followed by rule name (or ID), its parameter and the value delimited by colon (``:``)::

    --configure <rule_name>:<param_name>:<value>

For example::

    robocop --configure line-too-long:line_length:140 .

or more concise variant using rule ID instead of its name and short ``-c`` option::

    robocop -c 0508:line_length:140 .

which overwrites the value for the maximum line length (120 by default).

Some rules accept comma-separated values like::

    robocop -c todo-in-comment:markers:todo,changeme,refactor .

which changes the markers that trigger the rule when the marker appears in the comment.

If you need to provide a value with a space, wrap the whole configurable in quotes, like here::

    robocop -c "todo-in-comment:markers:Remove me,Fix this!" .

.. note::

    Configuration parameter (``--configure`` / ``-c``) can also be used to configure reports. More about it here :ref:`configuring-reports`.

Loading configuration from file
===============================

Robocop supports two formats of the configuration file: argument files and toml files. If argument file is not
provided using CLI, Robocop will try to find default configuration file using the following algorithm:

- if the directory contains ``.robocop`` file, load it
- otherwise, if the directory contains ``pyproject.toml`` file, load it
- otherwise, go to parent directory. Stop search if ``.git`` or top disk directory is found

``.robocop`` argument file
--------------------------

Argument file supports the same syntax as given from the CLI:

..  code-block::
    :caption: .robocop

    --include rulename
    # inline comment
    --reports all

You can load arguments for Robocop from file with ``--argumentfile / -A`` option and path to the argument file:

..  code-block::
    :caption: .robocop

    robocop --argumentfile argument_file.txt
    robocop -A path/to/file.txt

Argument file can contain path to another argument file. Argument file directory will be used to resolve
relative paths. For example if you're executing::

    > robocop -A config/robocop_options.txt

And ``config/robocop_options.txt`` contains following configuration:

..  code-block::
    :caption: config/robocop_options.txt

    --argumentfile base.txt
    --exclude section-out-of-order

``base.txt`` path will be resolved as ``config/base.txt``.

``pyproject.toml`` or TOML configuration file
---------------------------------------------

Robocop uses ``[tool.robocop]`` section. Options have the same names as the CLI arguments.

This configuration file can be loaded automatically (if your project has ``pyproject.toml`` file) or by
using ``--config`` option and providing path to the configuration file.

Example of TOML configuration file:

..  code-block::
    :caption: pyproject.toml

    [tool.robocop]
    paths = [
        "tests\\atest\\rules\\bad-indent",
        "tests\\atest\\rules\\duplicated-library"
    ]
    include = ['W0504', '*doc*']
    exclude = ["0203"]
    reports = [
        "rules_by_id",
        "scan_timer"
    ]
    ignore = ["ignore_me.robot"]
    ext-rules = ["path_to_external\\dir"]
    filetypes = [".txt", ".tsv"]
    threshold = "E"
    format = "{source}:{line}:{col} [{severity}] {rule_id} {desc} (name)"
    output = "robocop.log"
    configure = [
        "line-too-long:line_length:150",
        "0201:severity:E"
    ]
    no_recursive = true

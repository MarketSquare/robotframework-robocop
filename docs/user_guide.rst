User guide
==========
This is short overview of how to use Robocop together with links to more extensive documentation.

You can run lint scan on Robot Framework code by simply running::

    robocop path/to/file/files

Robocop accepts files or directories as path. You can also specify multiple paths::

    robocop file.robot resources/etc test.robot

Robocop will find and skip paths from `.gitignore` files.

Including or excluding rules
----------------------------

Rules can be included or excluded from command line. It is also possible to disable rule(s) from Robot Framework
source code. More in :ref:`including-rules`.

.. _configuration file:

Loading configuration from file
-------------------------------
.. dropdown:: How to load configuration from the file

    Robocop supports two formats of the configuration file: argument files and toml files. If argument file is not
    provided using CLI, Robocop will try to find default configuration file using the following algorithm:

    - if the directory contains ``.robocop`` file, load it
    - otherwise, if the directory contains ``pyproject.toml`` file, load it
    - otherwise, go to parent directory. Stop search if ``.git`` or top disk directory is found

    .. dropdown:: ``.robocop`` argument file

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

    .. dropdown:: ``pyproject.toml`` or toml configuration file

        Robocop uses ``[tool.robocop]`` section. Options have the same names as the CLI arguments.

        This configuration file can be loaded automatically (if your project have ``pyproject.toml`` file) or by
        using ``--config`` option and path to to the configuration file.

        Example toml configuration file:

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


Listing available rules
-----------------------
To get list of available rules (with enabled/disabled status) use ``-l / --list`` option:

..  code-block:: none

    > robocop --list
    Rule - 0201 [W]: missing-doc-keyword: Missing documentation in '{{ name }}' keyword (enabled)
    Rule - 0202 [W]: missing-doc-test-case: Missing documentation in '{{ name }}' test case (enabled)
    Rule - 0203 [W]: missing-doc-suite: Missing documentation in suite (enabled)
    (...)

If some of the rules are disabled from CLI it will be reflected in the output:

..  code-block:: none

    > robocop --exclude 02* --list
    Rule - 0201 [W]: missing-doc-keyword: Missing documentation in '{{ name }}' keyword (disabled)
    Rule - 0202 [W]: missing-doc-test-case: Missing documentation in '{{ name }}' test case (disabled)
    Rule - 0203 [W]: missing-doc-suite: Missing documentation in suite (disabled)
    Rule - 0301 [W]: not-allowed-char-in-name: Not allowed character '{{ character }}' found in {{ block_name }} name (enabled)
    (...)

Rules list can be filtered out by glob pattern:

..  code-block:: none

    > robocop --list tag*
    Rule - 0601 [W]: tag-with-space: Tag '{{ tag }}' should not contain spaces (enabled)
    Rule - 0602 [I]: tag-with-or-and: Tag '{{ tag }}' with reserved word OR/AND. Hint: make sure to include this tag using lowercase name to avoid issues (enabled)
    Rule - 0603 [W]: tag-with-reserved-word: Tag '{{ tag }}' prefixed with reserved word `robot:` (enabled)
    Rule - 0606 [I]: tag-already-set-in-test-tags: Tag 'mytag' is already set by Test Tags in suite settings (enabled)

Use ``-lc \ --list-configurables`` argument to list rules together with available configurable parameters. Optional pattern argument is also supported:

..  code-block:: none

    robocop --list-configurables empty-lines-between-sections
    Rule - 1003 [W]: empty-lines-between-sections: Invalid number of empty lines between sections ({{ empty_lines }}/{{ allowed_empty_lines }}) (enabled)
        Available configurables for this rule:
            empty_lines = 2
                type: int
                info: number of empty lines required between sections


To list only enabled or disabled rules:

..  code-block:: none

    > robocop -i tag-with* --list ENABLED
    Rule - 0601 [W]: tag-with-space: Tag '{{ tag }}' should not contain spaces (enabled)
    Rule - 0602 [I]: tag-with-or-and: Tag '{{ tag }}' with reserved word OR/AND. Hint: make sure to include this tag using lowercase name to avoid issues (enabled)
    Rule - 0603 [W]: tag-with-reserved-word: Tag '{{ tag }}' prefixed with reserved word `robot:` (enabled)

    > robocop -e inconsistent-assignment-in-variables --list-configurables DISABLED
    Rule - 0910 [W]: inconsistent-assignment-in-variables: The assignment sign is not consistent inside the variables section. Expected '{{ expected_sign }}' but got '{{ actual_sign }}' instead (disabled)
        assignment_sign_type = autodetect
            type: parse_assignment_sign_type
            info: possible values: 'autodetect' (default), 'none' (''), 'equal_sign' ('=') or space_and_equal_sign (' =')


Ignoring file
-------------
Path matching glob pattern can be ignored (or *skipped* during scan). You can pass list of patterns::

    robocop --ignore *.robot,resources/* --ignore special_file.txt

Format output message
---------------------

Format of rules output messages can be redefined. More in messages documentation: :ref:`rules`.

Configuring rules
-----------------

Rules are configurable. Severity of every rule message can be changed and also some of the rules have
optional parameters. More on this in :ref:`rules`.

Save output to file
-------------------

You can redirect output of Robocop to a file by using pipes (``>`` in unix) or by ``-o`` / ``--output`` argument::

  robocop --output robocop.log

Generating reports
------------------

You can generate reports after run. Available reports are described in :ref:`reports`.

Return status
-------------

..  code-block:: none

    Come quietly or there will be... trouble. - Robocop

Return status of Robocop depends on number of issues reported per given severity level and the quality gates.
Quality gates are the number specified for each severity (error, warning, info) that cannot be
exceeded. Every violation of quality gates increases the return code by 1 up to maximum of 255.
Default levels are following::

  quality_gate = {
            'E': 0,
            'W': 0,
            'I': -1
        }

Number -1 means that return status is not affected by number of issues for given message. Default values can be configured
by ``-c/--configure`` and ``return_status:quality_gate`` param::

  robocop --configure return_status:quality_gate:E=100:W=100:I=9

Preceding example configuration results in following levels::

  quality_gate = {
            'E': 100,
            'W': 100,
            'I': 9
        }

Fixing issues
-------------
Many issues in your code reported by Robocop can be fixed using auto-formatting tool, Robotidy. Check out the Robotidy [documentation](https://robotidy.readthedocs.io/en/stable/).

Language support
-----------------
Robot Framework 6.0 added support for Robot settings and headers translation. Robocop will not recognize translated names unless
it is properly configured. You can supply language code or name in the configuration using ``--language / --lang`` option::

    robocop --lang fi

Support multiple languages by either using ``language`` option twice or provide language code/name in comma separated list::

    robocop --lang pl --lang pt
    robocop --lang fi,pt

``pyproject.toml`` file accepts ``language`` array::

    [tool.robocop]
    language = [
        "pt",
        "fi"
    ]

Custom language file is currently not supported.

User guide
==========
This is short overview of how to use Robocop together with links to more extensive documentation.

You can run lint scan on Robot Framework code by simply running::

    robocop path/to/file/files

Robocop accepts files or directories as path. You can also specify multiple paths::

    robocop file.robot resources/etc test.robot

Including or excluding rules
----------------------------

Rules can be included or excluded from command line. It is also possible to disable rule(s) from Robot Framework
source code. More in :ref:`including-rules`.

Loading configuration from file
-------------------------------
You can load arguments for Robocop from file with::

    --argumentfile jenkins_args.txt

If no arguments are provided to Robocop it will try to find ``.robocop`` file and load it from there.
It will start looking from current directory and go up until it founds it or '.git' file is found. ``.robocop`` file
supports the same syntax as given from cli::

    --include rulename
    --reports all

If there is no ``.robocop`` file present it will try to load ``pyproject.toml`` file (if there is toml module installed).
Robocop use [tool.robocop] section. Options have the same names as CLI arguments. Example configuration file::

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
    filetypes = [".txt", ".csv"]
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
To get list of available rules (with enabled/disabled status) use ``-l / --list`` option::

    robocop --list
    Rule - 0201 [W]: missing-doc-keyword: Missing documentation in keyword (enabled)
    Rule - 0202 [W]: missing-doc-testcase: Missing documentation in test case (enabled)
    Rule - 0203 [W]: missing-doc-suite: Missing documentation in suite (enabled)
    (...)

If some of the rules are disabled from CLI it will be reflected in output::

    robocop --exclude 02* --list
    Rule - 0201 [W]: missing-doc-keyword: Missing documentation in keyword (disabled)
    Rule - 0202 [W]: missing-doc-testcase: Missing documentation in test case (disabled)
    Rule - 0203 [W]: missing-doc-suite: Missing documentation in suite (enabled)
    (...)

Rules list can be filtered out by glob pattern::

    robocop --list tag*
    Rule - 0601 [W]: tag-with-space: Tags should not contain spaces (enabled)
    Rule - 0602 [I]: tag-with-or-and: Tag with reserved word OR/AND. Hint: make sure to include this tag using lowercase name to avoid issues (enabled)
    Rule - 0603 [W]: tag-with-reserved: Tag prefixed with reserved word `robot:`. Only allowed tag with this prefix is robot:no-dry-run (enabled)
    Rule - 0606 [I]: tag-already-set-in-force-tags: This tag is already set by Force Tags in suite settings (enabled)

Use ``-lc \ --list-configurables`` argument to list rules together with available configurable parameters. Optional pattern argument is also supported::

    robocop --list-configurables empty-lines-between-section
    Rule - 1003 [W]: empty-lines-between-sections: Invalid number of empty lines between sections (%d/%d) (enabled).
        Available configurable(s) for this rule:
            empty_lines

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
optional parameters. More on this in :ref:`checkers`.

Save output to file
-------------------

You can redirect output of Robocop to a file by using pipes (``>`` in unix) or by ``-o`` / ``--output`` argument::

  robocop --output robocop.log

Generating reports
------------------

You can generate reports after run. Available reports are described in :ref:`reports`.

Return status
-------------

::

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


***************
Getting started
***************

This is a short overview of how to use Robocop (with links to more extensive documentation).

You can run lint scan on Robot Framework code by simply running::

    robocop path/to/file/files

Robocop accepts files or directories as path. You can also specify multiple paths::

    robocop file.robot resources/etc test.robot

Robocop will find and skip paths from `.gitignore` files.

An example of the output the tool can produce::

    \Users\OCP\test.robot:7:1 [W] 0509 Section '*** Variables ***' is empty (empty-section)
    \Users\OCP\test.robot:22:1 [E] 0801 Multiple test cases with name "Simple Test" (first occurrence in line 17) (duplicated-test-case)
    \Users\OCP\test.robot:42:1 [E] 0810 Both Task(s) and Test Case(s) section headers defined in file (both-tests-and-tasks)
    \Users\OCP\test.robot:48:1 [W] 0302 Keyword 'my keyword' does not follow case convention (wrong-case-in-keyword-name)
    \Users\OCP\test.robot:51:13 [I] 0606 Tag 'mytag' is already set by Test Tags in suite settings (tag-already-set-in-test-tags)

    Found 5 issues: 2 ERRORs, 2 WARNINGs, 1 INFO.

.. note::

    In some examples of the run command, the dot ``.`` at the represents a path to the current directory.

Rules management
================

Including or excluding rules
----------------------------

Rules can be included or excluded from the command line.
Use ``--include`` / ``--exclude`` options to include or exclude rules (or use their short variants ``-i`` / ``-e``), for example::

    robocop --include missing-doc-test-case .

Instead of the whole name of the rule, you can also use the rule ID. In that case, the above example would look like this::

    robocop -i 0202 .

More in :ref:`including-rules`.

Disabling rules from source code
--------------------------------

It is also possible to disable rule(s) from Robot Framework source code.
Use a comment followed by ``robocop`` and optionally a rule that is going to be disabled, e.g.::

    *** Keywords ***
    Display Sentence
        [Arguments]      ${sentence}
        ${one-liner}     Parse Sentence  ${sentence}  # robocop: disable=hyphen-in-variable-name
        Print To Welcome Page   ${one-liner}

Learn more about disablers here - :ref:`disablers`.

Listing rules
-------------

To quickly see the list of all the rules, run::

    robocop --list

or short version ``robocop -l``.

You can provide a ``pattern`` to filter the rules that you are interested in, e.g. ``robocop -l *doc*``.

Read more about how to list the rules in :ref:`listing-rules`.

.. note::

    All Robocop rules are also nicely available here at :ref:`rules list`.

Handling output
===============

Format output message
---------------------

Format of rules output messages can be redefined. More in messages documentation: :ref:`output-message-format`.

Save output to file
-------------------

You can redirect output of Robocop to a file by using pipes (``>`` in unix) or by ``-o`` / ``--output`` argument::

  robocop --output robocop.log .

Generating reports
------------------

You can generate reports after run. Available reports are described in :ref:`reports`.

.. _return_status:

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

  robocop --configure return_status:quality_gate:E=10:W=100:I=9

Preceding example configuration results in following levels::

  quality_gate = {
            'E': 10,
            'W': 100,
            'I': 9
        }

Ignoring files
==============

Path matching glob pattern can be ignored (or *skipped* during scan). You can pass list of patterns::

    robocop --ignore *.robot,resources/* --ignore special_file.txt

Fixing issues
=============

Many issues in your code reported by Robocop can be fixed using auto-formatting tool, Robotidy.
Check out the Robotidy `documentation <https://robotidy.readthedocs.io/en/stable/>`_.

Language support
================

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

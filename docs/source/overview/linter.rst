.. _linter:

*******
Linter
*******

Lint your Robot Framework code by running::

    robocop check

It will recursively discover all ``*.robot`` and ``*.resource`` files in the current directory.

You can also use path specific path or paths::

    robocop check file.robot resources/etc test.robot

Robocop will also find and skip paths from `.gitignore` files. It is possible to configure how Robocop discover
files using various options - see X # TODO.

An example of the output the tool can produce::

    # TODO: Update output after extended is introduced
    \Users\OCP\test.robot:7:1 [W] 0509 Section '*** Variables ***' is empty (empty-section)
    \Users\OCP\test.robot:22:1 [E] 0801 Multiple test cases with name "Simple Test" (first occurrence in line 17) (duplicated-test-case)
    \Users\OCP\test.robot:42:1 [E] 0810 Both Task(s) and Test Case(s) section headers defined in file (both-tests-and-tasks)
    \Users\OCP\test.robot:48:1 [W] 0302 Keyword 'my keyword' does not follow case convention (wrong-case-in-keyword-name)
    \Users\OCP\test.robot:51:13 [I] 0606 Tag 'mytag' is already set by Test Tags in suite settings (tag-already-set-in-test-tags)

    Found 5 issues: 2 ERRORs, 2 WARNINGs, 1 INFO.

Rules management
================

Select rules
------------

Rules can be selected or ignored using configuration.
Use ``--select`` and ``--ignore`` to select only rules to run or run all default rules except ignored ones:

.. tab-set::

    .. tab-item:: Cli

        .. code:: shell

             robocop check --select rule1 --select rule2 --select rule3 --ignore rule2

    .. tab-item:: Configuration file

        .. code:: toml

            [robocop.lint]
            select = [
                "rule1",
                "rule2",
                "rule3"
            ]
            ignore = [
                "rule2"
            ]

In this example we are selecting ``rule1``, ``rule2`` and ``rule3``. Additionally ``rule2`` is ignored so Robocop
will only report ``rule1`` and ``rule3``.

More in :ref:`including-rules`.

Disabling rules from source code
--------------------------------

It is also possible to disable rule(s) from Robot Framework source code.
Use ``# robocop: off`` and optionally a rule that is going to be disabled, e.g.::

    *** Keywords ***
    Display Sentence
        [Arguments]      ${sentence}
        ${one-liner}     Parse Sentence  ${sentence}  # robocop: off=hyphen-in-variable-name
        Print To Welcome Page   ${one-liner}

Learn more about disablers here - :ref:`disablers`.

List rules
----------

To see the list of all the rules, run:

.. code:: shell

    robocop list rules

You can provide a ``--pattern`` to filter the rules that you are interested in, e.g.
``robocop list rules --pattern *doc*``.

Read more about how to list the rules in :ref:`list-rules`.

.. note::

    All Robocop rules are also nicely available here at :ref:`rules list`.

Handling output
===============

Format output message
---------------------

Format of rules output messages can be redefined. More in messages documentation: :ref:`output-message-format`.

Save output to file
-------------------

# TODO
You can redirect output of Robocop to a file by using pipes (``>`` in unix) or by ``-o`` / ``--output`` argument::

  robocop --output robocop.log

Generating reports
------------------

You can generate reports after run. Available reports are described in :ref:`reports`.

.. _return_status:

Language support
================

Robot Framework 6.0 added support for Robot settings and headers translation. Robocop will not recognize translated names unless
it is properly configured. You can supply language code or name in the configuration using ``--language / -l`` option:

.. tab-set::

    .. tab-item:: Cli

        .. code:: shell

             robocop check --language fi

    .. tab-item:: Configuration file

        .. code:: toml

            [robocop.lint]
            language = [
                "fi"
            ]

Support multiple languages by either using ``language`` option multiple times:


.. tab-set::

    .. tab-item:: Cli

        .. code:: shell

            robocop check -l pl -l pt

    .. tab-item:: Configuration file

        .. code:: toml

            [robocop.lint]
            language = [
                "pl",
                "pt"
            ]

Custom language file is currently not supported.

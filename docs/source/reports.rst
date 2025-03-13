.. _reports:

*******
Reports
*******

Reports are configurable summaries after a Robocop scan. For example, it can display a total number of issues discovered.
They are dynamically loaded during setup according to a configuration.

Report class collects diagnostic messages from a linter and can optionally parse them. At the end of the scan it will
generate the report.

To enable report use ``-r`` / ``--reports`` argument and provide the name of the report.
You can use multiple reports with separate arguments (``-r report1 -r report2``) or comma-separated list
(``-r report1,report2``). For example:

.. tab-set::

    .. tab-item:: Cli

        .. code:: shell

            robocop check --reports rules_by_id,some_other_report

    .. tab-item:: Configuration file

        .. code:: toml

            [robocop.lint]
            reports = [
                "rules_by_id",
                "some_other_report"
            ]

.. note::

    Reports can be only enabled and configured from the configuration file closest to the current working directory.
    If you configure reports in multiple configuration files, only one configuration file will apply.

To enable all default reports use ``--reports all``.  Non-default reports can be only enabled using their name.

The order of the reports is preserved. For example, if you want ``timestamp`` report to be printed before any
other reports, you can use the following configuration:

.. tab-set::

    .. tab-item:: Cli

        .. code:: shell

            robocop check --reports timestamp,all

    .. tab-item:: Configuration file

        .. code:: toml

            [robocop.lint]
            reports = [
                "timestamp",
                "all"
            ]

List available reports
======================

Print a list of all reports with their configured status by using ``list reports`` command::

    robocop list reports --reports all

You can filter the list using ``--enabled`` / ``--disabled`` flags::

    robocop list reports --reports timestamp,sarif --disabled

.. _configuring-reports:

Configuring reports
===================

It is possible to configure some of the reports using ``--configure`` (or ``-c``) option followed by report name,
its parameter and the value::

    robocop check --configure <report_name>.<param_name>=<value>

For example:

.. tab-set::

    .. tab-item:: Cli

        .. code:: shell

            robocop check --configure sarif.report_filename=robocop_sarif.json --reports sarif

    .. tab-item:: Configuration file

        .. code:: toml

            [robocop.lint]
            reports = [
                "sarif"
            ]
            configure = [
                "sarif.report_filename=robocop_sarif.json"
            ]

configures ``report_filename`` parameter to ``robocop_sarif.json`` for ``sarif`` report.

Disable all reports
-------------------

When handling multiple configuration sources it may be possible to inherit reports configuration that we don't want to
use. Use special keyword ``None`` to not run any reports even if configured::

    robocop check --reports sarif,all,None

Comparing results
------------------

Several reports allows to compare current run with the previous run. Use ``compare_runs`` report name to enable it. # TODO: make it an option

Example output::

    Found 18 (-3) issues: 13 (-4) INFOs, 5 (+1) WARNINGs.

    Issues by ID:
    MISC12 [I] (unnecessary-string-conversion)    : 10 (+0)
    NAME01 [W] (not-allowed-char-in-name)         : 2 (+0)
    VAR02 [I] (unused-variable)                   : 2 (-4)
    VAR03 [W] (variable-overwritten-before-usage) : 2 (+1)
    TAG05 [I] (could-be-test-tags)                : 1 (+0)
    VAR11 [W] (overwriting-reserved-variable)     : 1 (+0)

Robocop stores previous result in cache directory.
Cache directory is stored in the different location depending on the platform:

- Linux: ``"~/.cache/robocop"``
- macOS: ``"~/Library/Caches/robocop"``
- Windows: ``"C:\\Users\\<username>\\AppData\\Local\\robocop"``

Saving the results is disabled by default and can be enabled with ``--persistent`` flag:

.. tab-set::

    .. tab-item:: Cli

        .. code:: shell

            robocop check --persistent

    .. tab-item:: Configuration file

        .. code:: toml

            [robocop.lint]
            persistent = true

Only the previous run for the current working directory is saved.

To used stored results to compare with current run, enable ``compare_runs`` report:

.. tab-set::

    .. tab-item:: Cli

        .. code:: shell

            robocop check --reports all,compare_runs

    .. tab-item:: Configuration file

        .. code:: toml

            [robocop.lint]
            reports = [
                "all",
                "compare_runs"
            ]

Reports list
============

.. automodule:: robocop.linter.reports

Print issues
------------

.. automodule:: robocop.linter.reports.print_issues.PrintIssuesReport

----

Rules by ID
-----------

.. automodule:: robocop.linter.reports.rules_by_id_report.RulesByIdReport

----

Rules by severity
-----------------

.. automodule:: robocop.linter.reports.rules_by_severity_report.RulesBySeverityReport

----

Return status
-------------

.. automodule:: robocop.linter.reports.return_status_report.ReturnStatusReport

----

Execution time
--------------

.. automodule:: robocop.linter.reports.time_taken_report.TimeTakenReport

----

File statistics
---------------

.. automodule:: robocop.linter.reports.file_stats_report.FileStatsReport

----

Robocop version
---------------

.. automodule:: robocop.linter.reports.robocop_version_report.RobocopVersionReport

----

Report timestamp
----------------

.. automodule:: robocop.linter.reports.timestamp_report.TimestampReport

----

JSON export
-----------

.. automodule:: robocop.linter.reports.json_report.JsonReport

----

SARIF export
------------

.. automodule:: robocop.linter.reports.sarif_report.SarifReport


----

.. _gitlab:

Gitlab
------

.. automodule:: robocop.linter.reports.gitlab.GitlabReport

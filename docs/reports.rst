.. _reports:

Reports
========

Reports are configurable summaries after a Robocop scan. For example, it can display a total number of issues discovered.
They are dynamically loaded during setup according to a configuration.

Report class may collect rules messages from linter and parse it. At the end of the scan it will generate the report.

To enable report use ``-r`` / ``--reports`` argument and provide the name of the report.
You can use multiple reports with separate arguments (``-r report1 -r report2``) or comma-separated list
(``-r report1,report2``). Example::

    robocop --reports rules_by_id,some_other_report path/to/file.robot

To enable all default reports use ``--reports all``.  Non-default reports can be only enabled using their name.

The order of the reports is preserved. For example, if you want ``timestamp`` report to be printed before any
other reports, you can use the following configuration::

    robocop --reports timestamp,all src.robot

Print a list of all reports with their configured status by using ``--list-reports``::

    robocop --reports all --list-reports

You can filter the list using optional ``ENABLED``/``DISABLED`` argument::

    robocop --reports timestamp,sarif --list-reports DISABLED

Compare report results
----------------------

Reports results can be compared with the previous run. Example output::

    Found 18 (-3) issues: 13 (-4) INFOs, 5 (+1) WARNINGs.

    Issues by ID:
    I0923 (unnecessary-string-conversion)     : 10 (+0)
    W0922 (variable-overwritten-before-usage) : 2 (+1)
    I0920 (unused-variable)                   : 2 (-4)
    W0301 (not-allowed-char-in-name)          : 2 (+0)
    W0324 (overwriting-reserved-variable)     : 1 (+0)
    I0605 (could-be-test-tags)                : 1 (+0)


Robocop stores previous result in cache directory.
Cache directory is stored in the different location depending on the platform::

    - Linux: "~/.cache/robocop"
    - macOS: "~/Library/Caches/robocop"
    - Windows: "C:\\Users\\<username>\\AppData\\Local\\robocop"

Saving the results is disabled by default and can be enabled with ``--persistent`` flag::

    robocop --persistent

or in the TOML configuration file::

    [tool.robocop]
    persistent = true

Only the previous run for the current working directory is saved.

To used stored results to compare with current run, enable ``compare_runs`` report::

    robocop --reports all,compare_runs

.. automodule:: robocop.reports

.. autoclass:: robocop.reports.rules_by_id_report.RulesByIdReport

.. autoclass:: robocop.reports.rules_by_severity_report.RulesBySeverityReport

.. autoclass:: robocop.reports.return_status_report.ReturnStatusReport

.. autoclass:: robocop.reports.time_taken_report.TimeTakenReport

.. autoclass:: robocop.reports.file_stats_report.FileStatsReport

.. autoclass:: robocop.reports.robocop_version_report.RobocopVersionReport

.. autoclass:: robocop.reports.timestamp_report.TimestampReport

.. autoclass:: robocop.reports.json_report.JsonReport

.. autoclass:: robocop.reports.sarif_report.SarifReport

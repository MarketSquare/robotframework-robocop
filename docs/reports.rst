.. _reports:

*******
Reports
*******

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

List available reports
======================

Print a list of all reports with their configured status by using ``--list-reports``::

    robocop --reports all --list-reports

You can filter the list using optional ``ENABLED``/``DISABLED`` argument::

    robocop --reports timestamp,sarif --list-reports DISABLED

.. _configuring-reports:

Configuring reports
===================

Similarly as rules, reports can also be configured. The same ``--configure`` (or ``-c``) option is used followed by report name, its parameter and the value::

    robocop --configure <report_name>:<param_name>:<value>

For example::

    robocop --configure return_status:quality_gate:E=100:W=100:I=9

configures ``quality_gate`` parameter and sets new threshold values for different severities of the rules (see more at :ref:`return_status`).

There are also other configurable reports like ``timestamp`` or ``json_report``. More about them below.

Reports list
============

Compare results
---------------

**Report name**: ``compare_runs``

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
Cache directory is stored in the different location depending on the platform:

- Linux: ``"~/.cache/robocop"``
- macOS: ``"~/Library/Caches/robocop"``
- Windows: ``"C:\\Users\\<username>\\AppData\\Local\\robocop"``

Saving the results is disabled by default and can be enabled with ``--persistent`` flag::

    robocop --persistent

or in the TOML configuration file::

    [tool.robocop]
    persistent = true

Only the previous run for the current working directory is saved.

To used stored results to compare with current run, enable ``compare_runs`` report::

    robocop --reports all,compare_runs

.. automodule:: robocop.reports

Rules by ID
-----------

.. automodule:: robocop.reports.rules_by_id_report.RulesByIdReport

Rules by severity
-----------------

.. automodule:: robocop.reports.rules_by_severity_report.RulesBySeverityReport

Return status
-------------

.. automodule:: robocop.reports.return_status_report.ReturnStatusReport

Execution time
--------------

.. automodule:: robocop.reports.time_taken_report.TimeTakenReport

File statistics
---------------

.. automodule:: robocop.reports.file_stats_report.FileStatsReport

Robocop version
---------------

.. automodule:: robocop.reports.robocop_version_report.RobocopVersionReport

Report timestamp
----------------

.. automodule:: robocop.reports.timestamp_report.TimestampReport

JSON export
-----------

.. automodule:: robocop.reports.json_report.JsonReport

SARIF export
------------

.. automodule:: robocop.reports.sarif_report.SarifReport

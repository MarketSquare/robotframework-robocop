Disable reports from the configuration (#1072)
----------------------------------------------

It is now possible to disable all reports with special keyword ``None``::

    robocop --reports all,None

It is useful when Robocop joins configuration from multiple sources (configuration files or cli) but user want to
override any configured report and do not run any report.

.. _cli-options:

CLI options
===========

To see all available command line interface (CLI) options, execute::

    robocop -h

or::

    robocop --help

and you will be shown with the following output:

.. TODO: Generate help output dynamically

..  code-block:: none

    usage: robocop [-i RULES] [-e RULES] [-rules EXT_RULES] [-nr] [-r REPORTS] [-f FORMAT] [-c CONFIGURABLE] [-l [PATTERN]] [-lc [PATTERN]] [-lr] [-o PATH] [-ft FILETYPES] [-t THRESHOLD] [-A PATH] [-g PATH] [-gd PATTERN]
               [--language LANGUAGE] [-h] [-v] [-vv]
               [paths ...]

    Static code analysis tool for Robot Framework

    Required parameters:
      paths                 List of paths (files or directories) to be parsed by Robocop.

    Optional parameters:
      -i RULES, --include RULES
                            Run Robocop only with specified rules. You can define rule by its name or id.
                            Glob patterns are supported.
      -e RULES, --exclude RULES
                            Ignore specified rules. You can define rule by its name or id.
                            Glob patterns are supported.
      -rules EXT_RULES, --ext-rules EXT_RULES
                            List of paths with custom rules.
      -nr, --no-recursive   Use this flag to stop scanning directories recursively.
      -r REPORTS, --reports REPORTS
                            Generate reports after scan.
                            You can enable reports by listing them in comma-separated list:
                            --reports rules_by_id,rules_by_error_type,scan_timer
                            To enable all reports use all:
                            --reports all
      -f FORMAT, --format FORMAT
                            Format of output message. You can use placeholders to change the way an issue is reported.
                            Default: {source}:{line}:{col} [{severity}] {rule_id} {desc} ({name})
      -c CONFIGURABLE, --configure CONFIGURABLE
                            Configure checker or report with parameter value. Usage:
                            -c message_name_or_id:param_name:param_value
                            Examples:
                            -c line-too-long:line_length:150
                            --configure 0101:severity:E
      -l [PATTERN], --list [PATTERN]
                            List all available rules. You can use optional PATTERN argument to match rule names
                            (for example --list *doc*).
                            PATTERN can be also ENABLED/DISABLED keyword to list only enabled/disabled rules.
      -lc [PATTERN], --list-configurables [PATTERN]
                            List all available rules with configurable parameters.
                            You can use optional PATTERN argument to match rule names (for example --list *doc*).
                            PATTERN can be also ENABLED/DISABLED keyword to list only enabled/disabled rules.
      -lr, --list-reports   List all available reports.
      -o PATH, --output PATH
                            Path to output file.
      -ft FILETYPES, --filetypes FILETYPES
                            Comma-separated list of file extensions to be scanned by Robocop
      -t THRESHOLD, --threshold THRESHOLD
                            Disable rules below given threshold. Available message levels: I < W < E
      -A PATH, --argumentfile PATH
                            Path to file with arguments.
      --config PATH
                            Path to TOML configuration file.
      -g PATH, --ignore PATH
                            Ignore file(s) and path(s) provided. Glob patterns are supported.
      -gd PATTERN, --ignore-default PATTERN
                            Paths ignored by default. A regular expression to exclude directories on file search.
                            An empty value means no path is excluded. Default: (\.direnv|\.eggs|\.git|\.hg|\.nox|\.tox|\.venv|venv|\.svn)
      --language LANGUAGE, --lang LANGUAGE
                            Parse Robot Framework files using additional languages.
      -h, --help            Print this help message and exit.
      -v, --version         Display Robocop version.
      -vv, --verbose        Display extra information during execution.

    For full documentation visit: https://robocop.readthedocs.io/en/latest/

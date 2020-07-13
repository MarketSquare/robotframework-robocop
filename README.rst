Robocop
===============
.. contents::
   :local:
   
Introduction
------------

Robcop is tool for performing static code analysis of Robot Framework code.

It uses official Robot Framework parsing api to parse files and run number of checks, 
looking for potential errors or violations to code quality standards.
 
 Hosted on github: https://github.com/bhirsz/robotframework-robocop
 
Install
-------

You can install robocop by running::

    pip install robotframework-robocop


Usage
-----
robocop will execute all checks on provided list of paths::

    robocop tests test.robot other_dir/subdir


Including or excluding rules
----------------------------
You can include or exclude particular rules using rule name or id.
Rules are matched in similar way how Robot Framework include/exclude arguments.

Described examples::

    robocop --include missing-keyword-doc test.robot

All rules will be ignored except missing-keyword-doc rule.::

    robocop --exclude missing-keyword-doc test.robot


Only missing-keyword-doc rule will be ignored.

Robocop supports glob patterns::

    robocop --include *doc* test.robot

All rules will be ignored except those with doc in its name (like missing-doc-keyword, too-long-doc..).

You can provide list of rules in comma seperated format or repeat argument::

    robocop --include rule1,rule2,rule3 --exclude rule2  --exclude rule1 test.robot

You can use short names instead::

    robocop -i rule1 -e rule2 test.robot

Generating reports
------------------

You can generate reports after run. Available reports:

* rules_by_id

It will print summary of all issues found, ordered by most frequent issue

Example::

    Issues by ids:
    W0502 (too-little-calls-in-keyword) : 5
    W0201 (missing-doc-keyword)         : 4
    E0401 (parsing-error)               : 3
    W0301 (invalid-char-in-name)        : 2
    E0901 (keyword-after-return)        : 1

* rules_by_error_type

It will print general summary of total number of issues and number of issues per issue type

Example::

    Found 15 issues: 11 WARNING(s), 4 ERROR(s).


To enable report use -r or --report argument and name of the report.
You can use separate arguments (-r report1 -r report2) or comma separated list (-r report1,report2)

Disabling rules in file
-----------------------
It is possible to disable rule for particular line or lines::

    Some Keyword  # robocop: disable:rule1,rule2

In this example no messages will be printed for this line for rules named rule1,rule2.
You can disable all rules with::

    Some Keyword  # robocop: disable

When used in new line without any indent it will start ignore block::

    # robocop: disable=rule1

All matched rules will be disabled until enable command::

    # robocop: enable=rule1

    or:

    # robocop: enable

Ignore blocks can partly overlap. Rule name and rule id can be used interchangeably.

Format output message
---------------------
Output message can be defined with -f / --format argument. Default value::

    {source}:{line}:{col} [{severity}] {msg_id} {desc}

Configure message severity
--------------------------

Configure message severity with -c/--configure argumen and message id or name::

    --configure 0502:severity:error  --configure some_rule:severity:i

Available severity levels, case insensitive::

    Error: error, e
    Warning: warning, w
    Info: info, i
    Fatal: fatal, f


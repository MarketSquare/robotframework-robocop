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
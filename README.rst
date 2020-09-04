|Unit tests|

.. image:: docs/images/robocop_logo_small.png

Robocop
===============

.. include-this-block-in-docs-start

.. contents::
   :local:

Introduction
------------

Robocop is a tool that performs static code analysis of Robot Framework code.

It uses official Robot Framework parsing API to parse files and run number of checks,
looking for potential errors or violations to code quality standards.

    Hosted on `GitHub
    <https://github.com/bhirsz/robotframework-robocop>`_

Values
-------
Original *RoboCop* - a fictional cybernetic police officer - was following 3 prime directives
which also drive the progress of Robocop:

    First Directive: **Serve the public trust**

Which lies behind the creation of the project - to **serve** developers and testers as a tool to build applications they can **trust**

    Second Directive: **Protect the innocent**

**The innocent** testers and developers have no intention to produce ugly code but sometimes, you know, it just happens,
so Robocop is there to **protect** them

    Third Directive: **Uphold the law**

Following the coding guidelines established in the project are something very important to keep the code clean,
readable and understandable by others and Robocop can help to **uphold the law**

Requirements
------------

Python 3.6+ and Robot Framework 3.2.1+.

Installation
------------

You can install Robocop simply by running::

    pip install robotframework-robocop


Usage
-----

Robocop will execute all checks on provided list of paths::

    robocop tests test.robot other_dir/subdir

.. include-this-block-in-docs-end

Main features
-------------

- including/excluding rules from command line with the support for glob patterns::

    --include *missing* -i W0507 --exclude rule,rule2 -e *doc*

- disabling rules directly from source code

    Ignoring rules in one line::

        This is Keyword  # robocop: disable=not-capitalized-keyword-name

    Ignoring all rules or selected ones::

        Log  ${var}
        Log  ${var}  # robocop: disable
        log  ${var}  # robocop: disable=0301,0302

    Ignoring whole blocks or even files::

        # robocop: disable=unnecessary-default-tags,0102
        *** Settings ***
        Library  RobotLibrary.py

        # robocop: enable=0102


- filtering out all rules below given severity level::

     --threshold E

- customized format of output message::

    --format {source}:{line}:{col} [{severity}] {rule_id} {desc}

- configurable return status for every severity level::

    --configure return_status:quality_gate:E=2:W=39

- generating customized reports::

    --reports rules_by_id,rules_by_error_type

    Issues by ids:
    W0902 (ineven-indent)                : 5
    E0904 (nested-for-loop)              : 4
    W0302 (not-capitalized-keyword-name) : 4

    Found 12 issue(s): 9 WARNING(s), 4 ERROR(s).

- configurable lint rules

    --configure 0507:line_length:100 -c ineven-indent:severity:W

- external rules support::

    --ext_rules path/to/your/rules.py -rules supports_many_paths.py

- output redirection to file
- loading arguments from file
- configurable scanned filetypes

Documentation
-------------

Full documentation available `here <https://robocop.readthedocs.io>`_.

.. |Unit tests| image:: https://github.com/bhirsz/robotframework-robocop/workflows/Unit%20tests/badge.svg?branch=master
   :target: https://github.com/bhirsz/robotframework-robocop/actions?query=workflow%3A%22Unit+tests%22

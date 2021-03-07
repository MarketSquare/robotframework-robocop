.. Badges

|Unit tests| |Codecov| |PyPI| |Python versions| |License|

.. image:: https://raw.githubusercontent.com/MarketSquare/robotframework-robocop/master/docs/images/robocop_logo_small.png
   :alt: Robocop logo

Robocop
===============

.. include-this-block-in-docs-start

.. contents::
   :local:

Introduction
------------

Robocop is a tool that performs static code analysis of `Robot Framework
<https://github.com/robotframework/robotframework>`_ code.

It uses official `Robot Framework parsing API
<https://robot-framework.readthedocs.io/en/latest/>`_ to parse files and run number of checks,
looking for potential errors or violations to code quality standards.

    Hosted on `GitHub
    <https://github.com/MarketSquare/robotframework-robocop>`_

Documentation
-------------

Full documentation available `here <https://robocop.readthedocs.io>`_.

Values
-------
Original *RoboCop* - a fictional cybernetic police officer - was following 3 prime directives
which also drive the progress of Robocop linter:

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

Robocop runs by default from the current directory and it discovers supported files recursively.
You can simply run::

    robocop
    
All command line options can be displayed in help message by executing::

    robocop -h

.. include-this-block-in-docs-end

Example Output
--------------

Executing command::

    robocop --report rules_by_error_type tests\test.robot

Will result in following output::

    C:\OCP_project\tests\test.robot:7:0 [W] 0509 Section is empty
    C:\OCP_project\tests\test.robot:22:0 [E] 0801 Multiple test cases with name "Simple Test" in suite
    C:\OCP_project\tests\test.robot:42:0 [E] 0810 Both Task(s) and Test Case(s) section headers defined in file
    C:\OCP_project\tests\test.robot:48:0 [W] 0302 Keyword name should be capitalized
    C:\OCP_project\tests\test.robot:51:13 [I] 0606 This tag is already set by Force Tags in suite settings

    Found 5 issue(s): 2 WARNING(s), 2 ERROR(s), 1 INFO(s).

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
        Log  ${var}  # noqa

    Ignoring whole blocks or even files::

        # robocop: disable=unnecessary-default-tags,0102
        *** Settings ***
        Library  RobotLibrary.py

        # robocop: enable=0102


- filtering out all rules below given severity level::

     --threshold E

- customized format of output message::

    --format "{source}:{line}:{col} [{severity}] {rule_id} {desc}"

- configurable return status for every severity level::

    --configure return_status:quality_gate:E=2:W=39

- generating customized reports::

    --reports rules_by_id,rules_by_error_type

    Issues by ids:
    W1007 (uneven-indent)                : 5
    E0904 (nested-for-loop)              : 4
    W0302 (not-capitalized-keyword-name) : 4

    Found 12 issue(s): 9 WARNING(s), 4 ERROR(s).

- configurable lint rules::

    --configure 0507:line_length:100 -c uneven-indent:severity:W

- external rules support::

    --ext_rules path/to/your/rules.py -rules supports_many_paths.py

- output redirection to file::

    --output robocop.log

- loading arguments from file::

    --argumentfile jenkins_args.txt

- configurable scanned filetypes::

    --filetypes .txt,.rst

- paths matching pattern can be ignored::

    --ignore *.robot,resources/* --ignore special_file.txt

----

::

    Excuse me, I have to go. Somewhere there is a crime happening. - Robocop

.. Badges links

.. |Unit tests|
   image:: https://img.shields.io/github/workflow/status/MarketSquare/robotframework-robocop/Unit%20tests/master
   :alt: GitHub Workflow Unit Tests Status
   :target: https://github.com/MarketSquare/robotframework-robocop/actions?query=workflow%3A%22Unit+tests%22

.. |Codecov|
   image:: https://img.shields.io/codecov/c/github/MarketSquare/robotframework-robocop/master
   :alt: Code coverage on master branch

.. |PyPI|
   image:: https://img.shields.io/pypi/v/robotframework-robocop?label=version
   :alt: PyPI package version

.. |Python versions|
   image:: https://img.shields.io/pypi/pyversions/robotframework-robocop
   :alt: Supported Python versions

.. |License|
   image:: https://img.shields.io/pypi/l/robotframework-robocop
   :alt: PyPI - License


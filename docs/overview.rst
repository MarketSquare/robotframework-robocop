Introduction
------------

Robocop is a tool that performs static code analysis of `Robot Framework
<https://github.com/robotframework/robotframework>`_ code.

It uses official `Robot Framework parsing API
<https://robot-framework.readthedocs.io/en/stable/>`_ to parse files and runs number of checks,
looking for potential errors or violations to code quality standards (commonly referred as *linting issues*).

    Hosted on `GitHub
    <https://github.com/MarketSquare/robotframework-robocop>`_

Documentation
-------------

Full documentation is available `here <https://robocop.readthedocs.io>`_.

Requirements
------------

Python 3.7+ and Robot Framework 3.2.2+.

Installation
------------

You can install Robocop simply by running::

    pip install -U robotframework-robocop

Usage
-----

Robocop runs by default from the current directory and it discovers supported files recursively.
You can simply run::

    robocop

All command line options can be displayed in help message by executing::

    robocop -h

or found in our :ref:`cli-options` documentation.

Example Output
--------------

Executing command::

    robocop --report rules_by_error_type test.robot

Will result in following output:

..  code-block:: none

    \Users\OCP\test.robot:7:1 [W] 0509 Section '*** Variables ***' is empty (empty-section)
    \Users\OCP\test.robot:22:1 [E] 0801 Multiple test cases with name "Simple Test" (first occurrence in line 17) (duplicated-test-case)
    \Users\OCP\test.robot:42:1 [E] 0810 Both Task(s) and Test Case(s) section headers defined in file (both-tests-and-tasks)
    \Users\OCP\test.robot:48:1 [W] 0302 Keyword 'my keyword' does not follow case convention (wrong-case-in-keyword-name)
    \Users\OCP\test.robot:51:13 [I] 0606 Tag 'mytag' is already set by Test Tags in suite settings (tag-already-set-in-test-tags)

    Found 5 issues: 2 ERRORs, 2 WARNINGs, 1 INFO.

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

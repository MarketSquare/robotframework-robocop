Introduction
============

Robocop |:robot:| is a tool that performs static code analysis and formatting of `Robot Framework
<https://github.com/robotframework/robotframework>`_ code.

It uses official `Robot Framework parsing API
<https://robot-framework.readthedocs.io/en/stable/>`_ to parse files and runs number of checks,
looking for potential errors or violations to code quality standards (commonly referred as *linting issues*). It can
also format code to ensure consistent code style.

    Hosted on `GitHub
    <https://github.com/MarketSquare/robotframework-robocop>`_ |:medal:|

Requirements
============

Python 3.9+ |:snake:| and Robot Framework 4+ |:robot:|.

Installation
============

You can install Robocop simply by running::

    pip install -U robotframework-robocop

Usage
=====

Robocop discovers supported files from the current directory and its sub-directories.

You can simply run:

..  code-block:: none

    robocop check
    robocop format

All command line commands and options can be displayed in help message by executing::

    robocop -h

Refer to overview pages to read more (:ref:`linter`, :ref:`formatter`).

Shell autocompletion
====================

It is possible use shell autocompletion by installing it for the current shell::

    robocop --install-completion

Values
======

Original *RoboCop* - a fictional cybernetic police officer |:cop:| - was following 3 prime directives
which also drive the progress of Robocop linter:

    First Directive: **Serve the public trust** |:family_man_woman_girl_boy:|

Which lies behind the creation of the project - to **serve** developers and testers as a tool to build applications they can **trust**

    Second Directive: **Protect the innocent** |:baby:|

**The innocent** testers and developers have no intention to produce ugly code but sometimes, you know, it just happens,
so Robocop is there to **protect** them

    Third Directive: **Uphold the law** |:classical_building:|

Following the coding guidelines established in the project are something very important to keep the code clean,
readable and understandable by others and Robocop can help to **uphold the law**

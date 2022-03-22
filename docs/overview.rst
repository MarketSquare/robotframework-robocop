Introduction
------------

Robocop is a tool that performs static code analysis of `Robot Framework
<https://github.com/robotframework/robotframework>`_ code.

It uses official `Robot Framework parsing API
<https://robot-framework.readthedocs.io/en/stable/>`_ to parse files and run number of checks,
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

Python 3.6+ and Robot Framework 3.2.2+.

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

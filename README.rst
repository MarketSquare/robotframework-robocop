.. image:: docs/images/robocop_logo.png
   :scale: 25 %
   :alt: Robocop logo
   :align: center

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

    * including/excluding rules from command line or source code
    * customized format of output message
    * generating customized reports
    * configurable lint rules
    * output can be redirected to file

Documentation
-------------

Full documentation available `here <https://robocop.readthedocs.io>`_ .
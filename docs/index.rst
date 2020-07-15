.. Robocop documentation master file, created by
   sphinx-quickstart on Wed Jul 15 12:39:37 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Robocop's documentation!
===================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. include:: ../README.rst

Robocop lint rules
------------------
Robocop lint rules are called checkers internally. Each checker can scan for multiple related issues
(like LengthChecker checks both for min and max length of keyword). You can refer to specific messages
reported by checkers by its name or id (for example `0501` or `too-long-keyword`).

Each message have configurable severity and optionally other parameters.

.. toctree::
   :maxdepth: 2
   :caption: Checkers:

   checkers

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

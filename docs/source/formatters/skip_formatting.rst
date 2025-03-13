.. _skip_formatting:

Skip formatting
================

It is possible to skip formatting on code of given type. Skip options apply to all instances of the
given code - for example it is possible to skip formatting on all documentation. If you want to disable formatting
on specific lines, see :ref:`disablers`.

To see what types are possible to skip, see ``Skip formatting`` sections in each formatter documentation.

.. _skip option:

Skip option
-----------

Option that allows to skip configured type of the code. Supported types:

* --skip documentation
* --skip return-values
* --skip settings
* --skip arguments
* --skip setup
* --skip teardown
* --skip timeout
* --skip template
* --skip return
* --skip tags
* --skip comments
* --skip block-comments

Example usage:

.. code:: shell

    robocop format -c NormalizeSeparators.skip=documentation

It is possible to use global option to skip formatting for every formatter that supports it:

.. code:: shell

    robocop format --skip documentation

Both options are configurable using configuration file (:ref:`config-file`).

.. code-block:: toml

    [tool.robocop.format]
    skip = ["documentation"]
    configure = [
        "NormalizeSeparators.skip=documentation"
    ]

.. _skip keyword call:

Skip keyword call
------------------

Comma-separated list of keyword call names that should not be formatted. Names will be
normalized before search (spaces and underscores removed, lowercase).

With this configuration::

    robotidy -c AlignTestCasesSection.skip_keyword_call=ExecuteJavascript,catenate

All instances of ``Execute Javascript`` and ``Catenate`` keywords will not be formatted.

It is possible to use global option to skip formatting for every transformer that supports it::

    robotidy --skip-keyword-call Name --skip-keyword-call othername src

Configuration file
~~~~~~~~~~~~~~~~~~~~

Both options are configurable using configuration file (:ref:`config-file`).

.. code-block:: toml

    [tool.robocop.format]
    skip-keyword-call = [
        "GlobalSkip",
        "supports spaces too"
    ]
    configure = [
        "AlignKeywordsSection.skip_keyword_call=Name,othername"
    ]

.. _skip keyword call pattern:

Skip keyword call pattern
-------------------------

Comma-separated list of keyword call name patterns that should not be formatted. The keyword names are not normalized.
If you're using different case for the same keyword ("Keyword" and "keyword") or using both spaces and underscores, it is
recommended to use proper regex flags to match it properly.

With this configuration::

    robotidy -c AlignKeywordsSection.skip_keyword_call_pattern=^First,(i?)contains\s?words src

All instances of keywords that start with "First" or contain "contains words" (case insensitive, space optional) will
not be formatted.

> Note that list is comma-separated - it is currently not possible to provide regex with ``,``.

It is possible to use global option to skip formatting for every transformer that supports it::

    robotidy --skip-keyword-call-pattern ^Second --skip-keyword-call-pattern (i?)contains\s?words src

Configuration file
~~~~~~~~~~~~~~~~~~~~

Both options are configurable using configuration file (:ref:`config-file`).

.. code-block:: toml

    [tool.robocop.format]
    skip-keyword-call-pattern = [
        "^Second",
        "(i?)contains\s?words"
    ]
    configure = [
        "AlignKeywordsSection.skip_keyword_call_pattern=first,secondname"
    ]

.. _skip sections:

Skip sections
---------------

Option that disables formatting of the selected sections. Example usage::

    robotidy -c NormalizeSeparators.skip_sections=variables src

It is possible to use global option to skip formatting for every transformer that supports it::

    robotidy --skip-sections=keywords,testcases src

Section names can be provided using comma separated list: settings,variables,testcases,keywords,comments.

Configuration file
~~~~~~~~~~~~~~~~~~~~
Both options are configurable using configuration file (:ref:`config-file`).

.. code-block:: toml

    [tool.robocop.format]
    skip-sections = "comments"
    configure = [
        "NormalizeSeparators.skip_sections=tasks,keywords"
    ]

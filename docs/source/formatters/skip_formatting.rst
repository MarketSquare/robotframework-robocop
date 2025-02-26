.. _skip_formatting:

Skip formatting
================

.. rubric:: Skip formatting

It is possible to skip formatting on code that matches given criteria. Skip options apply to all instances of the
given code - for example it is possible to skip formatting on all documentation. If you want to disable formatting
on specific lines, see :ref:`disablers`.

To see what types are possible to skip, see ``Skip formatting`` sections in each transformer documentation.

.. _skip documentation:

Skip documentation
-------------------

Flag that disables formatting of the documentation. Example usage::

    robocop format -c NormalizeSeparators:skip_documentation=True

It is possible to use global flag to skip formatting for every transformer that supports it::

    robocop check --skip-documentation

Configuration file
~~~~~~~~~~~~~~~~~~~~

Both options are configurable using configuration file (:ref:`config-file`).

.. code-block:: toml

    [tool.robocop]
    skip-documentation = true
    configure = [
        "NormalizeSeparators : skip_documentation = False"
    ]

.. _skip return values:

Skip return values
-------------------

Flag that disables formatting of the return values (assignments). Example usage::

    robotidy -c AlignKeywordsSection:skip_return_values=True src

It is possible to use global flag to skip formatting for every transformer that supports it::

    robotidy --skip-return-values src

Configuration file
~~~~~~~~~~~~~~~~~~~~

Both options are configurable using configuration file (:ref:`config-file`).

.. code-block:: toml

    [tool.robotidy]
    skip-return-values = true
    configure = [
        "AlignKeywordsSection : skip_return_values = False"
    ]

.. _skip keyword call:

Skip keyword call
------------------

Comma-separated list of keyword call names that should not be formatted. Names will be
normalized before search (spaces and underscores removed, lowercase).

With this configuration::

    robotidy -c AlignTestCasesSection:skip_keyword_call=ExecuteJavascript,catenate

All instances of ``Execute Javascript`` and ``Catenate`` keywords will not be formatted.

It is possible to use global option to skip formatting for every transformer that supports it::

    robotidy --skip-keyword-call Name --skip-keyword-call othername src

Configuration file
~~~~~~~~~~~~~~~~~~~~

Both options are configurable using configuration file (:ref:`config-file`).

.. code-block:: toml

    [tool.robotidy]
    skip-keyword-call = [
        "GlobalSkip",
        "supports spaces too"
    ]
    configure = [
        "AlignKeywordsSection : skip_keyword_call = Name,othername"
    ]

.. _skip keyword call pattern:

Skip keyword call pattern
-------------------------

Comma-separated list of keyword call name patterns that should not be formatted. The keyword names are not normalized.
If you're using different case for the same keyword ("Keyword" and "keyword") or using both spaces and underscores, it is
recommended to use proper regex flags to match it properly.

With this configuration::

    robotidy -c AlignKeywordsSection:skip_keyword_call_pattern=^First,(i?)contains\s?words src

All instances of keywords that start with "First" or contain "contains words" (case insensitive, space optional) will
not be formatted.

> Note that list is comma-separated - it is currently not possible to provide regex with ``,``.

It is possible to use global option to skip formatting for every transformer that supports it::

    robotidy --skip-keyword-call-pattern ^Second --skip-keyword-call-pattern (i?)contains\s?words src

Configuration file
~~~~~~~~~~~~~~~~~~~~

Both options are configurable using configuration file (:ref:`config-file`).

.. code-block:: toml

    [tool.robotidy]
    skip-keyword-call-pattern = [
        "^Second",
        "(i?)contains\s?words"
    ]
    configure = [
        "AlignKeywordsSection : skip_keyword_call_pattern = first,secondname"
    ]

.. _skip settings:

Skip settings
-------------------

Flag that disables formatting of the settings. Example usage::

    robotidy -c AlignTestCasesSection:skip_settings=True src

It is possible to use global flag to skip formatting for every transformer that supports it::

    robotidy --skip-settings src

Formatting of the settings can be also skipped based on the type of the settings.

The name of the option is ``skip_<setting_name>`` (for example ``skip_arguments``).
Following types are possible to skip:

- arguments - ``[Arguments]``
- setup - ``[Setup]``
- teardown - ``[Teardown]``
- template - ``[Template]``
- timeout - ``[Timeout]``
- return - ``[Return]`` or ``RETURN``
- tags - ``[Tags]``

Configuration file
~~~~~~~~~~~~~~~~~~~~

Option is configurable using configuration file (:ref:`config-file`).

Skip formatting of all settings:

.. code-block:: toml

    [tool.robotidy]
    skip-settings = true
    configure = [
        "AlignTestCasesSection : skip_settings = False"
    ]

Skip formatting of selected settings:

.. code-block:: toml

    [tool.robotidy]
    skip-setup = true
    skip-teardown = true
    configure = [
        "AlignTestCasesSection : skip_setup = False"
        "AlignKeywordsSection : skip_arguments = True"
    ]

.. _skip comments:

Skip comments and block comments
---------------------------------

Flag that disables formatting of the comments and block comments. Example usage::

    robotidy -c NormalizeSeparators:skip_comments=True src

It is possible to use global flag to skip formatting for every transformer that supports it::

    robotidy --skip-comments src

The comment is considered any standalone comment. Comments that start from column 0 are considered to be
block comments:

.. code-block:: robotframework

    *** Keywords ***
    # block comment
    Keyword
        [Documentation]    doc
        # standalone comment
        Log   Logging statement

    # block comment    with extra spaces
    #            that will be not formatted

Configuration file
~~~~~~~~~~~~~~~~~~~~
Both options are configurable using configuration file (:ref:`config-file`).

.. code-block:: toml

    [tool.robotidy]
    skip-comments = true
    configure = [
        "NormalizeSeparators : skip_block_comments = False"
    ]

.. _skip sections:

Skip sections
---------------

Option that disables formatting of the selected sections. Example usage::

    robotidy -c NormalizeSeparators:skip_sections=variables src

It is possible to use global option to skip formatting for every transformer that supports it::

    robotidy --skip-sections=keywords,testcases src

Section names can be provided using comma separated list: settings,variables,testcases,keywords,comments.

Configuration file
~~~~~~~~~~~~~~~~~~~~
Both options are configurable using configuration file (:ref:`config-file`).

.. code-block:: toml

    [tool.robotidy]
    skip-sections = "comments"
    configure = [
        "NormalizeSeparators : skip_sections = tasks,keywords"
    ]

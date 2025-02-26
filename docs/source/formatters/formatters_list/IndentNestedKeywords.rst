.. _IndentNestedKeywords:

IndentNestedKeywords
================================

Format indentation inside run keywords variants such as ``Run Keywords`` or ``Run Keyword And Continue On Failure``.

.. |FORMATTERNAME| replace:: IndentNestedKeywords
.. include:: disabled_hint.txt

Keywords inside run keywords variants are detected and whitespace is formatted to outline them.

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Test Cases ***
            Test
                Run Keyword    Run Keyword If    ${True}    Run keywords   Log    foo    AND    Log    bar    ELSE    Log    baz

    .. tab-item:: After

        .. code:: robotframework

            *** Test Cases ***
            Test
                Run Keyword
                ...    Run Keyword If    ${True}
                ...        Run keywords
                ...            Log    foo
                ...            AND
                ...            Log    bar
                ...    ELSE
                ...        Log    baz

Handle AND inside Run Keywords
-------------------------------

``AND`` argument inside ``Run Keywords`` can be handled in different ways. It is controlled via ``indent_and``
parameter.
You can configure it using ``indent_and``::

    robocop format -c IndentNestedKeywords.indent_and=keep_and_indent

Following values are available:

- ``indent_and=split`` splits ``AND`` to new line,
- ``indent_and=split_and_indent`` splits ``AND`` and additionally indents the keywords,
- ``indent_and=keep_in_line`` keeps ``AND`` next to the previous keyword.

.. tab-set::

    .. tab-item:: indent_and=split (default)

        .. code:: robotframework

            *** Test Cases ***
            Test
                Run keywords
                ...    Log    foo
                ...    AND
                ...    Log    bar

    .. tab-item:: indent_and=split_and_indent

        .. code:: robotframework

            *** Test Cases ***
            Test
                Run keywords
                ...        Log    foo
                ...    AND
                ...        Log    bar

    .. tab-item:: indent_and=keep_in_line

        .. code:: robotframework

            *** Test Cases ***
            Test
                Run keywords
                ...    Log    foo    AND
                ...    Log    bar


Skip formatting settings
-------------------------

To skip formatting run keywords inside settings (such as ``Suite Setup``, ``[Setup]``, ``[Teardown]`` etc.) set
``skip_settings`` to ``True``::

    robocop format -c IndentNestedKeywords.skip_settings:True


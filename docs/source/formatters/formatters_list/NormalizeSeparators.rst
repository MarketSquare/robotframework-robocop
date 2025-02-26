.. _NormalizeSeparators:

NormalizeSeparators
================================

Normalize separators and indents.

.. |FORMATTERNAME| replace:: NormalizeSeparators
.. include:: enabled_hint.txt

All separators (pipes included) are converted to fixed length of 4 spaces (configurable via global option
``--spacecount``). To separately configure the indentation, use ``--indent`` global option.

.. note::
    There are formatters that also affect separator lengths - for example ``AlignSettingsSection``. ``NormalizeSeparators``
    is used as a base and then potentially overwritten by behaviours of other formatters. If you only want to have fixed
    separator lengths (without aligning) then only run this formatter without running the others.

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Settings ***
            Library  library.py  WITH NAME          alias

            Force Tags           tag
            ...   tag

            Documentation  doc
            ...      multi
            ...  line

            *** Test Cases ***
            Test case
              [Setup]  Keyword
               Keyword  with  arg
               ...  and  multi  lines
                 [Teardown]          Keyword

            Test case with structures
                FOR  ${variable}  IN  1  2
                Keyword
                 IF  ${condition}
                   Log  ${stuff}  console=True
              END
               END

    .. tab-item:: After

        .. code:: robotframework

            *** Settings ***
            Library    library.py    WITH NAME    alias

            Force Tags    tag
            ...    tag

            Documentation    doc
            ...    multi
            ...    line

            *** Test Cases ***
            Test case
                [Setup]    Keyword
                Keyword    with    arg
                ...    and    multi    lines
                [Teardown]    Keyword

            Test case with structures
                FOR    ${variable}    IN    1    2
                    Keyword
                    IF    ${condition}
                        Log    ${stuff}    console=True
                    END
                END

Configure separator
--------------------

By configuring a global option ``spacecount``, you can change the default separator length::

    robocop format --spacecount 8

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Settings ***
            Library  library.py  WITH NAME          alias

            Force Tags           tag
            ...   tag

    .. tab-item:: After

        .. code:: robotframework

            *** Settings ***
            Library        library.py        WITH NAME        alias

            Force Tags        tag
            ...        tag

Indentation
------------

By default, indentation is the same as ``spacecount`` value (default ``4`` spaces). To configure it, use ``--indent``::

    robocop format --indent 4

Combine it with ``spacecount`` to set whitespace separately for indent and separators::

    robocop format --indent 4 --spacecount 2

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Keywords ***
            Keyword
              FOR     ${var}  IN RANGE     10
                Keyword With  ${var}
              END

    .. tab-item:: After

        .. code:: robotframework

            *** Keywords ***
            Keyword
                FOR  ${var}  IN RANGE  10
                    Keyword With  ${var}
                END

Flatten multi line statements
------------------------------

By default ``NormalizeSeparators`` only updates the separators and leave any multi line intact. It is possible to
flatten multi line statements into single line using ``flatten_lines`` option::

    > robocop format -c NormalizeSeparators.flatten_lines=True

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Keywords ***
            Keyword
                Keyword Call    1  2
                  ...    1  # comment
                ...    2          3

    .. tab-item:: After - default (flatten_lines = False)

        .. code:: robotframework

            *** Keywords ***
            Keyword
                Keyword Call    1    2
                ...    1    # comment
                ...    2    3

    .. tab-item:: After (flatten_lines = True)

        .. code:: robotframework

            *** Keywords ***
            Keyword
                Keyword Call    1    2    1    2    3  # comment

Align new lines
---------------

It is possible to align new lines to the first line. This alignment will be overwritten if you have transformers affecting
alignment enabled, such as:

- AlignKeywordsSection
- AlignSettingsSection
- AlignTemplatedTestCases
- AlignTestCasesSection
- AlignVariablesSection

You can enable it using ``align_new_line`` parameter::

    > robocop format --configure NormalizeSeparators.align_new_line=True

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Test Cases ***
            Test
                [Tags]    tag
                ...  tag2

            *** Keywords ***
            Keyword
                [Arguments]    ${argument1}
                ...    ${argument2} ${argument3}
                Keyword Call    argument
                ...  arg2
                ...    arg3


    .. tab-item:: After - default (align_new_line=False)

        .. code:: robotframework

            *** Test Cases ***
            Test
                [Tags]    tag
                ...    tag2

            *** Keywords ***
            Keyword
                [Arguments]    ${argument1}
                ...    ${argument2}   ${argument3}
                Keyword Call    argument
                ...    arg2
                ...    arg3

    .. tab-item:: After (align_new_line=True)

        .. code:: robotframework

            *** Test Cases ***
            Test
                [Tags]    tag
                ...       tag2

            *** Keywords ***
            Keyword
                [Arguments]    ${argument1}
                ...            ${argument2}   ${argument3}
                Keyword Call    argument
                ...             arg2
                ...             arg3

Skip formatting
----------------

It is possible to use the following arguments to skip formatting of the code:

- :ref:`skip option`
- :ref:`skip keyword call`
- :ref:`skip keyword call pattern`
- :ref:`skip sections`

Documentation is formatted by default. To disable formatting the separators inside documentation, and to only format
indentation, set ``skip_documentation`` to ``True``::

    robocop format --configure NormalizeSeparators.skip_documentation=True

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            TEST_TC
                [Argument]    ${a}    ${long_arg}
                [Documentation]     Test Doc.
                ...
                ...    Arguments:
                ...    a:               Argument A
                ...    long_arg:        Argument long_arg.
               Test Case Body

    .. tab-item:: skip_documentation=False (default)

        .. code:: robotframework

            TEST_TC
                [Argument]    ${a}    ${long_arg}
                [Documentation]     Test Doc.
                ...
                ...    Arguments:
                ...    a:    Argument A
                ...    long_arg:    Argument long_arg.
               Test Case Body

    .. tab-item:: skip_documentation=True

        .. code:: robotframework

            TEST_TC
                [Argument]    ${a}    ${long_arg}
                [Documentation]     Test Doc.
                ...
                ...    Arguments:
                ...    a:               Argument A
                ...    long_arg:        Argument long_arg.
               Test Case Body

It is also possible to use disablers (:ref:`disablers`) but ``skip`` option
makes it easier to skip all instances of given type of the code.

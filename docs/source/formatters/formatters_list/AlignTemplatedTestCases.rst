.. _AlignTemplatedTestCases:

AlignTemplatedTestCases
================================

Align suites with Test Template to columns.

For non-templated test cases use ``AlignTestCasesSection`` formatter. Test cases that are templated with
``[Template]`` setting should also use ``AlignTestCasesSection``.

.. |FORMATTERNAME| replace:: AlignTemplatedTestCases
.. include:: disabled_hint.txt

Examples:

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Settings ***
            Test Template    Templated Keyword

            *** Test Cases ***    baz    qux
            # some comment
            test1    hi    hello
            test2 long test name    asdfasdf    asdsdfgsdfg

    .. tab-item:: After

        .. code:: robotframework

            *** Settings ***
            Test Template    Templated Keyword

            *** Test Cases ***      baz         qux
            # some comment
            test1                   hi          hello
            test2 long test name    asdfasdf    asdsdfgsdfg
                                    bar1        bar2

Any argument in the same line as test case name will be used as column header for the alignment:

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Settings ***
            Test Template    Dummy

            *** Test Cases ***
            Test1    ARG1
                [Tags]    sanity
                [Documentation]  Validate Test1
            Test2    ARG2
                [Tags]    smoke
                [Documentation]  Validate Test2

    .. tab-item:: After

        .. code:: robotframework

            *** Settings ***
            Test Template    Dummy

            *** Test Cases ***
            Test1     ARG1
                      [Tags]              sanity
                      [Documentation]     Validate Test1
            Test2     ARG2
                      [Tags]              smoke
                      [Documentation]     Validate Test2

Align only test case section with named headers
------------------------------------------------

If you don't want to align test case section that does not contain header names then configure ``only_with_headers`` parameter::

    robocop format -c AlignTemplatedTestCases.only_with_headers=True

Fixed width of column
-------------------------

It's possible to set fixed minimal width of column. To configure it use ``min_width`` parameter::

    robocop format --configure AlignTemplatedTestCases.min_width=30

This configuration respects ``up_to_column`` parameter which only aligns columns up to configured ``up_to_column``
column.

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Test Cases ***    baz    qux
            # some comment
            test1    hi    hello
            test2 long test name    asdfasdf    asdsdfgsdfg
                bar1  bar2

    .. tab-item:: After

        .. code:: robotframework

            *** Test Cases ***            baz                           qux
            # some comment
            test1                         hi                            hello
            test2 long test name          asdfasdf                      asdsdfgsdfg
                                          bar1                          bar2

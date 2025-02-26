.. _NormalizeNewLines:

NormalizeNewLines
================================

Normalize new lines.

.. |FORMATTERNAME| replace:: NormalizeNewLines
.. include:: enabled_hint.txt

Ensure that there is exactly:

- ``section_lines = 1`` empty lines between sections,

- ``test_case_lines = 1`` empty lines between test cases,

- ``keyword_lines = test_case_lines`` empty lines between keywords.

Removes empty lines after section (and before any data) and appends 1 empty line at the end of file.

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            This data is ignored at runtime but should be preserved by Tidy.
            *** Variables ***
            # standalone      comment
            ${VALID}          Value
            # standalone

            *** Test Cases ***


            Test
                [Documentation]    This is a documentation
                ...    in two lines
                Some Lines
                No Operation
                [Teardown]    1 minute    args

            Test Without Arg
            Mid Test
                My Step 1    args    args 2    args 3    args 4    args 5    args 6
                ...    args 7    args 8    args 9    # step 1 comment

            *** Keywords ***
            Keyword
                No Operation
            Other Keyword
            Another Keyword
                There
                Are
                More
            *** Settings ***
            Library  library.py

    .. tab-item:: After

        .. code:: robotframework

            This data is ignored at runtime but should be preserved by Tidy.

            *** Variables ***
            # standalone      comment
            ${VALID}          Value
            # standalone

            *** Test Cases ***
            Test
                [Documentation]    This is a documentation
                ...    in two lines
                Some Lines
                No Operation
                [Teardown]    1 minute    args

            Test Without Arg

            Mid Test
                My Step 1    args    args 2    args 3    args 4    args 5    args 6
                ...    args 7    args 8    args 9    # step 1 comment

            *** Keywords ***
            Keyword
                No Operation

            Other Keyword

            Another Keyword
                There
                Are
                More

            *** Settings ***
            Library  library.py

Parameters ``section_lines``, ``test_case_lines`` and ``keyword_lines`` can be configured to other values::

    robocop format --configure NormalizeNewLines.section_lines=3

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Settings ***
            Library  Collections

            *** Keywords ***
            Keyword
                Log  stuff

    .. tab-item:: After

        .. code:: robotframework

            *** Settings ***
            Library  Collections



            *** Keywords ***
            Keyword
                Log  stuff


Consecutive empty lines inside settings, variables, keywords and test cases are also removed
(configurable via ``consecutive_lines = 1``).

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Settings ***

            Resource    resource.robot


            Default Tags    tag

            Documentation    doc




            *** Test Cases ***
            Test Capitalized

                Pass Execution

    .. tab-item:: After

        .. code:: robotframework

            *** Settings ***
            Resource    resource.robot

            Default Tags    tag

            Documentation    doc

            *** Test Cases ***
            Test Capitalized
                Pass Execution

If set to 0 all empty lines will be removed::

    robocop format --configure NormalizeNewLines.consecutive_lines=0

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Settings ***

            Resource    resource.robot


            Default Tags    tag

            Documentation    doc




            *** Test Cases ***
            Test Capitalized

                Pass Execution

    .. tab-item:: After

        .. code:: robotframework

            *** Settings ***
            Resource    resource.robot
            Default Tags    tag
            Documentation    doc

            *** Test Cases ***
            Test Capitalized
                Pass Execution

If the suite contains Test Template tests will not be separated by empty lines unless ``separate_templated_tests``
is set to True.

.. tab-set::

    .. tab-item:: separate_templated_tests=False (default)

        .. code:: robotframework

            *** Settings ***
            Test Template    Template For Tests In This Suite

            *** Test Cases ***
            Test    arg1   arg2
            Test Without Arg
            Mid Test
                My Step 1    args    args 2    args 3

    .. tab-item:: separate_templated_tests=True

        .. code:: robotframework

            *** Settings ***
            Test Template    Template For Tests In This Suite

            *** Test Cases ***
            Test    arg1   arg2

            Test Without Arg

            Mid Test
                My Step 1    args    args 2    args 3

Language header
----------------

Files that begin with the language marker are handled differently.
If the section contains only language marker and no more empty lines than the value of ``section_lines``,
it will be not transformed.
The following examples will not be formatted since the number of empty lines is lower or equal to default value of ``section_lines``:

.. tab-set::

    .. tab-item:: File with language marker and 0 empty lines

        .. code:: robotframework

            language: pl
            *** Ustawienia ***

    .. tab-item:: File with language marker and 2 empty lines

        .. code:: robotframework

            language: pl


            *** Ustawienia ***

Section will be formatted if it contains more empty lines than ``section_lines`` or has statements other than
language marker:

.. tab-set::

    .. tab-item:: File with language marker and 3 empty lines

        .. code:: robotframework

            language: pl



            *** Ustawienia ***

    .. tab-item:: After

        .. code:: robotframework

            language: pl


            *** Ustawienia ***

.. tab-set::

    .. tab-item:: File with language marker and extra comments

        .. code:: robotframework

            language: pl
            This file contains polish tests.
            *** Ustawienia ***

    .. tab-item:: After

        .. code:: robotframework

            language: pl
            This file contains polish tests.


            *** Ustawienia ***

Skip formatting
----------------

It is possible to use the following arguments to skip formatting of the code:

- :ref:`skip sections`

It is also possible to use disablers (:ref:`disablers`) but ``skip`` option
makes it easier to skip all instances of given type of the code.

.. _disablers:

*********
Disablers
*********

Rules can be disabled directly from Robot Framework code. It is similar to how ``# noqa`` comment works for
most linters.

It is possible to disable rule for particular line or lines::

    Some Keyword  # robocop: disable=rule1,rule2

In this example no message will be printed for this line for rules named ``rule1``, ``rule2``.

You can disable all rules with::

    Some Keyword  # robocop: disable

Ignore whole blocks of code by defining a disabler in the new line::

    # robocop: disable=rule1

All matched rules will be disabled until ``enable`` command::

    # robocop: enable=rule1

or::

    # robocop: enable

Ignored blocks can partly overlap. Rule name and rule id can be used interchangeably.

The disabler is aware of the context where it was called, and it will be enabled again at the end of the current code
block (such as keyword, test case, "for" and "while" loops and "if" statement). In the following example,
``wrong-case-in-keyword-name`` disabler will disable the rule only inside the "for" loop.

..  code-block:: robotframework
    :caption: example.robot

    *** Keywords ***
    Compare Table With CSV Files
        [Arguments]    ${table}    @{files}
        ${data}    Get Data From Table    ${table}
        FOR    ${file}    IN    @{files}
            # robocop: disable=wrong-case-in-keyword-name
            Table data should be in file     ${data}    ${file}
        END
        Should Be Equal    ${erorrs}    @{EMPTY}

It is possible to ignore whole file if you start file with ``# robocop: disable``.

..  code-block:: robotframework
    :caption: example.robot

    # robocop: disable=missing-doc-test-case

    *** Test Cases ***
    Some Test
        Keyword 1
        Keyword 2
        Keyword 3

    *** Keywords ***
    Keyword 1
        # robocop: disable
        Log  1

    Keyword 2
        Log  2

    # robocop: disable
    Keyword 3
        Log  3

    Keyword 4
        Log  4
    # robocop: enable

In this example we are disabling ``missing-doc-test-case`` rule in the whole file.
Also we are disabling all rules inside ``Keyword 1`` keyword and all lines between
``Keyword 3`` and ``Keyword 4`` keywords.

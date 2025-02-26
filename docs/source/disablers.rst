.. _disablers:

*********
Disablers
*********

Rules can be disabled directly from Robot Framework code.
A special comment needs to be placed in order to disable specific rules of Robocop.
The comments is always prefixed with ``robocop`` marker followed by ``off`` or ``on`` word keywords::

    # robocop: off

The keyword may optionally have specified rules, separated by comma::

    # robocop: off=rule1,rule2

The disablers are also context-aware, meaning that they turn off the Robocop rules for the related code block,
e.g. keyword, test case, or even for loops and if statements.

.. note::

    The disablers are similar to how ``# noqa`` comment works for most linters.

Disabling lines
---------------

It is possible to disable rule for particular line or lines::

    Some Keyword  # robocop: off=rule1,rule2

In this example no message will be printed for this line for rules named ``rule1``, ``rule2``.

You can disable all rules with::

    Some Keyword  # robocop: off

Enabling back
-------------

Ignore whole blocks of code by defining a disabler in the new line::

    # robocop: off=rule1

All matched rules will be disabled until ``on`` command::

    # robocop: on=rule1

or::

    # robocop: on

.. note::

    Previously, Robocop used ``enable`` and ``disable`` as disabler keywords. It is still supported, however ``on`` and
    ``off`` are recommended instead.

Disabling code blocks
---------------------

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
            # robocop: off=wrong-case-in-keyword-name
            Table data should be in file     ${data}    ${file}
        END
        Should Be Equal    ${erorrs}    @{EMPTY}

Disabling files
---------------

It is possible to ignore whole file if you put Robocop disabler in the first comment section, at the beginning of the
file.

..  code-block:: robotframework
    :caption: example.robot

    # robocop: off=missing-doc-test-case

    *** Test Cases ***
    Some Test
        Keyword 1
        Keyword 2
        Keyword 3

    *** Keywords ***
    Keyword 1
        # robocop: off
        Log  1

    Keyword 2
        Log  2

    # robocop: off
    Keyword 3
        Log  3

    Keyword 4
        Log  4
    # robocop: on

In this example we are disabling ``missing-doc-test-case`` rule in the whole file.
Also we are disabling all rules inside ``Keyword 1`` keyword and all lines between
``Keyword 3`` and ``Keyword 4`` keywords.

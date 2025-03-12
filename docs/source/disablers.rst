.. _disablers:

*********
Disablers
*********

Rules and formatters can be disabled directly from Robot Framework code. You can use special directives as a comment.

Use following directives to disable linting::

    # robocop: off
    # noqa

To disable formatting, use following directives::

    # fmt: off
    # robocop: fmt: off

The keyword may optionally have specified rules or formatters, separated by comma::

    # robocop: off=rule1, rule2
    # robocop: fmt: off=FormatterName

The disablers are also context-aware, meaning that they turn off the Robocop rules for the related code block,
e.g. keyword, test case, or even for loops and if statements.

.. note::

    The disablers are similar to how ``# noqa`` comment works for most linters.

Disabling lines
---------------

It is possible to disable rule or formatter for particular line or lines::

    Some Keyword  # robocop: off=rule1
    Some Keyword  # robocop: fmt: off=FormatterName

In this example no message will be printed for this line for rule named ``rule1`` and no formatting changes
will be applied by FormatterName formatter.

You can disable all rules and formatters with::

    Some Keyword  # robocop: off

Enabling back
-------------

Ignore whole blocks of code by defining a disabler in the new line::

    # robocop: off=rule1

Enable it again with ``on`` command::

    # robocop: on=rule1

or::

    # robocop: on

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

New unused-keyword rule (#1097)
-------------------------------

New I10101 ``unused-keyword`` community rule. This optional rule finds not used keywords defined in suites (robot files
with tests/tasks) or private keywords (keywords with ``robot:private`` tag).

For example::

    *** Test Cases ***
    Test that only non used keywords are reported
        Used Keyword

    *** Keywords ***
    Not Used Keyword  # this keyword will be reported as not used
        [Arguments]    ${arg}
        Should Be True    ${arg}>50


This rule will be developed in the future releases to cover other sources like resource files.

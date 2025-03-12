*** Settings ***
Documentation  Suite doc


*** Test Case ***
My templated test
    [Documentation]    This test is templated
    [Template]         Some Template
                       10     arg2
                       20     arg3
                       -30    arg4

My templated test2
    [Documentation]    This test is templated
    [Template]         Some Template
    10     arg2
    20     arg3
    -30    arg4


My templated test3
    [Documentation]    This test is templated
      [Template]         Some Template
    10     arg2
    20     arg3
    -30    arg4


My templated test4
    [Documentation]    This test is templated
    [Template]         Some Template
    10     arg2
   20     arg3
    -30    arg4


*** Keywords ***
My Keyword  # robocop: off
    [Documentation]  Some doc
    No Operation


My Keyword    # robocop: off
    [Documentation]  Some doc
    No Operation

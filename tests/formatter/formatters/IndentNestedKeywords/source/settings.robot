*** Settings ***
Suite Setup
...         Run Keywords    No Operation    No Operation
Suite Teardown    Run Keywords    Log    1    AND    Log    2  # comment1

Test Setup    Run Keywords    No Operation    No Operation
Test Teardown    Run Keywords    No Operation
...    No Operation  # comment1  comment2


*** Test Cases ***
Test
    [Setup]  Run Keyword If    ${True}    No Operation
    [Teardown]    Run Keywords    Log    1  # comment
    ...    AND    Log    2    # comment2
    No Operation

Test in line    [Setup]    Run Keyword   Log    1  # comment
    No Operation

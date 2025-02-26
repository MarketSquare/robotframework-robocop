*** Settings ***
Suite Setup    Run Keywords
...    No Operation
...    No Operation
# comment1
Suite Teardown    Run Keywords
...    Log    1
...    AND
...    Log    2

Test Setup    Run Keywords
...    No Operation
...    No Operation
# comment1  comment2
Test Teardown    Run Keywords
...    No Operation
...    No Operation


*** Test Cases ***
Test
    [Setup]    Run Keyword If    ${True}
    ...    No Operation
    [Teardown]    Run Keywords  # comment comment2
    ...    Log    1
    ...    AND
    ...    Log    2
    No Operation

Test in line    [Setup]    Run Keyword  # comment
    ...    Log    1
    No Operation

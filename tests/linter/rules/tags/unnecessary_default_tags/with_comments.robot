*** Settings ***
Documentation    doc
Default Tags    tag    # comment
...    othertag


*** Test Cases ***
Test
    [Tags]    sometag
    No Operation

Test 2
    [Tags]    other
    No Operation

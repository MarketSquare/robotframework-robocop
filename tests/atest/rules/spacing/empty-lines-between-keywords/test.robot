*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    One More


*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail

Keyword2
    No Operation


Keyword3
    No Operation

# Some comment
Keyword4
    No Operation


# Some comment
Keyword5
    No Operation
# Some comment
Keyword6
    No Operation
# Some comment
# Some comment
Keyword7
    No Operation

# Some comment
# Some comment
Keyword8
    No Operation


# Some comment
# Some comment
Keyword9
    No Operation

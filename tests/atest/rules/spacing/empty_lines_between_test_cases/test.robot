*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    One More
Test2
    Keyword


Test3
    Keyword

# Some comment
Test 4
    Keyword


# Some comment
Test 5
    Keyword
# Some comment
Test 6
    Keyword

# Some comment
# Some comment
Test 7
    Keyword
# Some comment
# Some comment
Test 8
    Keyword


# Some comment
# Some comment
Test 9
    Keyword

*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail

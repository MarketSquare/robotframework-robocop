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
    Keyword
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    Keyword
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}
    ...   ${var}


Keyword with comments at the end
    Pass
    Keyword
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    One More
    # comments
    # comments
    # comments
    # comments

Keyword with comments that are not part of the test
    Pass
    Keyword
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    One More
    # comments
    # comments
    # comments
    # comments

# standalone comment


Short Keyword
    No Operation
    # comment

# standalone comment


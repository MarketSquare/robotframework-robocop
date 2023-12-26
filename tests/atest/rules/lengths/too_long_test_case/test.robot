*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
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
    VAR    ${variable}    value

Test with comments at the end
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

Test with comments that are not part of the test
    [Documentation]  abc
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


Short test
    No Operation
    # comment

# standalone comment


*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail

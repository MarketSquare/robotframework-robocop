*** Settings ***
Suite Setup    Run Keyword If    ${condition}    Keyword


*** Test Cases ***
Test
    No Operation
    Run Keyword If    ${condition}    Keyword
    ...    ELSE IF    ${condition2}    Keyword2
    ...    ELSE    Keyword3

    [Teardown]    Run Keyword Unless  ${condition}  Keyword5


*** Keywords ***
Keyword
    No Operation
    # comment with runkeywordif
    ${var}    Run Keyword If    ${condition}    Keyword
    Run Keyword Unless    ${condition}    Keyword2
    BuiltIn.Run Keyword If  ${stuff}  Keyword

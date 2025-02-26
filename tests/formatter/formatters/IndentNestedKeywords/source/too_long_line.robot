*** Settings ***
Suite Setup
...         Run Keywords    No Operation    No Operation
Suite Teardown    Run Keywords    Log    1    AND    Keyword Call That Is Going Over Allowed Limit    ${myVeryLongDefinitionOfAnElement}    ${myVeryLongDefinitionOfAnElement}  # comment1

Test Setup    Run Keywords    No Operation    Keyword Call That Is Going Over Allowed Limit Keyword Call That Is Going Over Allowed Limit Keyword Call That Is Going Over Allowed Limit
Test Teardown    Run Keywords    Keyword Call That Is Going Over Allowed Limit Keyword Call That Is Going Over Allowed Limit Keyword Call That Is Going Over Allowed Limit
...    No Operation  # comment1  comment2


*** Test Cases ***
Multiple cases
    Run Keyword And Continue On Failure
    ...    Run Keyword If    ${True}
    ...      Run keywords
    ...        log    foo    AND
    ...        Keyword Call That Is Going Over Allowed Limit    ${myVeryLongDefinitionOfAnElement}    ${myVeryLongDefinitionOfAnElement}
    ...    ELSE
    ...      log    baz

ELSE markers
    Run Keyword And Continue On Failure
    ...    Run Keyword If    ${True}
    ...      Run Keyword If    ${False}
    ...        Keyword Call That Is Going Over Allowed Limit    ${myVeryLongDefinitionOfAnElement}    ${myVeryLongDefinitionOfAnElement}
    ...      ELSE IF  ${True}
    ...        Log  Else If
    ...    ELSE
    ...      Keyword Call That Is Going Over Allowed Limit    ${myVeryLongDefinitionOfAnElement}    ${myVeryLongDefinitionOfAnElement}

Settings
    [Setup]    Run Keyword If    ${True}
    ...    Element Should Contain    ${myVeryLongDefinitionOfAnElement}    ${addingTheSecondArgumentMakesThisLineTooLong}
    Step


*** Keywords ***
Keyword That Should Be Split After First Argument
    Wait Until Keyword Succeeds    30 sec    1 sec    Run Keywords    Reload Page    AND    Element Should Contain    ${myVeryLongDefinitionOfAnElement}    ${addingTheSecondArgumentMakesThisLineTooLong}

Keyword That Should Be Split On Every Line
    Wait Until Keyword Succeeds    30 sec    1 sec    Run Keywords    Reload Page    AND    Element Should Contain    ${myVeryLongDefinitionOfAnElementmyVeryLongDefinitionOfAnElementmyVeryLongDefinitionOfAnElement}    ${addingTheSecondArgumentMakesThisLineTooLong}

    # argument over max allowed length
    Wait Until Keyword Succeeds    30 sec    1 sec    Run Keywords    Reload Page    AND    Element Should Contain    ${myVeryLongDefinitionOfAnElementmyVeryLongDefinitionOfAnElementmyVeryLongDefinitionOfAnElementmyVeryLongDefinitionOfAnElementmyVeryLongDefinitionOfAnElementmyVeryLongDefinitionOfAnElement}    ${addingTheSecondArgumentMakesThisLineTooLong}

Settings
    [Teardown]    Run Keywords  # comment comment2
    ...    Element Should Contain    ${myVeryLongDefinitionOfAnElement}    ${addingTheSecondArgumentMakesThisLineTooLong}    ${addingTheSecondArgumentMakesThisLineTooLong}
    ...    AND
    ...    Log    1

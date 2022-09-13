*** Settings ***
Suite Setup    Run Keywords    some keyword  AND  SOME_Keyword


*** Test Cases ***
Test with run keywords
    Run Keyword And Continue On Failure
    ...    Run Keyword if    ${True}
    ...      Run keywords
    ...        log    foo    AND
    ...        Log    bar
    ...    ELSE
    ...      log    baz

Settings
    [Setup]    Keyword
    [Teardown]    Run Keywords    keyword    Keyword

*** Keywords ***
Keyword With Run Keywords
    Builtin.Run Keyword_If    ${condition}    run Keywords    keyword    Keyword
    Run Keywords
    ...    Log    a
    ...    AND
    ...    log    b
    ...    AND
    ...    Log    c

More Branches
    Run Keyword If    ${condition
    ...         keyword
    ...    ELSE IF    ${other_cond}
    ...        other_keyword

Settings
    [Teardown]    Run Keywords    keyword    Keyword

Empty Run Keyword
    Run Keywords

Run Keyword With Variable
    Run Keywords    ${Variable}    ${variable}

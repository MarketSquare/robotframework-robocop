*** Settings ***
Suite Setup    Run Keywords    Some Keyword  AND  SOME Keyword


*** Test Cases ***
Test with run keywords
    Run Keyword And Continue On Failure
    ...    Run Keyword If    ${True}
    ...      Run Keywords
    ...        Log    foo    AND
    ...        Log    bar
    ...    ELSE
    ...      Log    baz

Settings
    [Setup]    Keyword
    [Teardown]    Run Keywords    Keyword    Keyword

*** Keywords ***
Keyword With Run Keywords
    Builtin.Run Keyword If    ${condition}    Run Keywords    Keyword    Keyword
    Run Keywords
    ...    Log    a
    ...    AND
    ...    Log    b
    ...    AND
    ...    Log    c

More Branches
    Run Keyword If    ${condition
    ...         Keyword
    ...    ELSE IF    ${other_cond}
    ...        Other Keyword

Settings
    [Teardown]    Run Keywords    Keyword    Keyword

Empty Run Keyword
    Run Keywords

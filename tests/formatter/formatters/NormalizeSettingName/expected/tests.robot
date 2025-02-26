*** Settings ***
Library
Documentation    This is example documentation
...              which is also multiline
Force Tags  tag1     tag2
Test Template  Keyword


*** Test Cases ***
Test
    [Setup]    Keyword2
    No Operation
    [Teardown]


*** Keywords ***
Keyword
    [Arguments]    ${arg}
    Pass

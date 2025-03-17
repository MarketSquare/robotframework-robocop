*** Settings ***
Test Template  Example


*** Test Cases ***
Example  argument=abc
    [Documentation]  Documentation text
Second test  argument=abc
    [Documentation]  Documentation text


*** Test Cases ***    ARG1    ARG2    [Documentation]           [Tags]
TestA                 aaa     AAA     Prints some message       tagA
TestB                 bbb     BBB     Prints another message    tagB


*** Keywords ***
Example
  [Arguments]  ${argument}
  Log  ${argument}

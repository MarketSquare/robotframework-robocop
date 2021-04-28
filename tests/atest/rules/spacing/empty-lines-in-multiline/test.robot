*** Settings ***
Documentation    This is
...   multiline line

...  docs


*** Variables ***
%{variable}    a=1
...   b=2

...  c=2

${var}  10


*** Test Cases ***
Test case
    Multiline Keyword  1

    ...  2

*** Keywords ***
Keyword
    No Operation

Keyword 2
    [Arguments]  ${arg}

    ...    1
    ...    2

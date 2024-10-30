*** Variables ***
${amazing}    Hello world!

*** Test Cases ***
Test
    VAR    ${foo}    bar
    VAR    ${lorum}    ipsum    scope=LOCAL
    VAR    ${amazing}    Hello universe    scope=GLOBAL

*** Keywords ***
Keyword
    VAR    ${amazing}    Hello universe    scope=GLOBAL

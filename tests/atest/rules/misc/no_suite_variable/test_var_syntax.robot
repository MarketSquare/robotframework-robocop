*** Variables ***
${amazing}    Hello world!

*** Test Cases ***
Test
    VAR    ${foo}    bar
    VAR    ${lorum}    ipsum    scope=LOCAL
    VAR    ${amazing}    Hello universe    scope=SUITE

Test plural
    VAR    ${amazing}    Hello universe    scope=SUITES

*** Keywords ***
Keyword
    VAR    ${amazing}    Hello universe    scope=SUITE

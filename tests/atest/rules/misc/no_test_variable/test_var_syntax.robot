*** Variables ***
${amazing}    Hello world!

*** Test Cases ***
Test
    VAR    ${foo}    bar
    VAR    ${lorum}    ipsum    scope=LOCAL
    VAR    ${amazing}    Hello universe    scope=TEST

Using Task
    VAR    ${amazing}    Hello universe    scope=TASK

*** Keywords ***
Keyword
    VAR    ${amazing}    Hello universe    scope=TEST

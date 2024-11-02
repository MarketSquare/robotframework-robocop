*** Variables ***
${amazing}    Hello world!
${scope}    TEST

*** Test Cases ***
Test
    VAR    ${foo}    bar
    VAR    ${lorum}    ipsum    scope=LOCAL
    VAR    ${amazing}    Hello universe    scope=TEST
    VAR    ${amazing}    Hello universe    scope=test

Using Task
    VAR    ${amazing}    Hello universe    scope=TASK

Using misc ways of writing weird things
    VAR
    VAR    scope=TEST
    VAR    $without_braces
    VAR    $without_braces    scope=TEST
    VAR    ${no_value}    scope=invalid_scope
    VAR    ${no_value}    scope=TEST
    VAR    ${no_value}    scope=${scope}
    VAR    ${no_value}    scope=${{ 'TEST' }}

*** Keywords ***
Keyword
    VAR    ${amazing}    Hello universe    scope=TEST

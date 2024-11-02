*** Variables ***
${amazing}    Hello world!
${scope}    SUITE

*** Test Cases ***
Test
    VAR    ${foo}    bar
    VAR    ${lorum}    ipsum    scope=LOCAL
    VAR    ${amazing}    Hello universe    scope=SUITE
    VAR    ${amazing}    Hello universe    scope=suite

Test plural
    VAR    ${amazing}    Hello universe    scope=SUITES

Using misc ways of writing weird things
    VAR
    VAR    scope=SUITE
    VAR    $without_braces
    VAR    $without_braces    scope=SUITE
    VAR    ${no_value}    scope=invalid_scope
    VAR    ${no_value}    scope=SUITE
    VAR    ${no_value}    scope=${scope}
    VAR    ${no_value}    scope=${{ 'SUITE' }}

*** Keywords ***
Keyword
    VAR    ${amazing}    Hello universe    scope=SUITE

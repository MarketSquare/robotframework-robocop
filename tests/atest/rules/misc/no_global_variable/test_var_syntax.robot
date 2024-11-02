*** Variables ***
${amazing}    Hello world!
${scope}    GLOBAL

*** Test Cases ***
Test
    VAR    ${foo}    bar
    VAR    ${lorum}    ipsum    scope=LOCAL
    VAR    ${amazing}    Hello universe    scope=GLOBAL
    VAR    ${amazing}    Hello universe    scope=global

Using misc ways of writing weird things
    VAR
    VAR    scope=GLOBAL
    VAR    $without_braces
    VAR    $without_braces    scope=GLOBAL
    VAR    ${no_value}    scope=invalid_scope
    VAR    ${no_value}    scope=GLOBAL
    VAR    ${no_value}    scope=${scope}
    VAR    ${no_value}    scope=${{ 'GLOBAL' }}

*** Keywords ***
Keyword
    VAR    ${amazing}    Hello universe    scope=GLOBAL

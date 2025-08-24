*** Settings ***
Documentation       doc


*** Test Cases ***
Test
    VAR    ${short_variable_name}    value
    VAR    ${loong_but_still_acceptable_variable_name}    value
    VAR    ${some_even_loooooonger_local_variable_name}    value

    FOR    ${i}    IN RANGE    ${10}
        VAR    ${some_even_loooooonger_local_variable_name}    value
    END

    TRY
        Something
        VAR    ${some_even_loooooonger_local_variable_name}    value
    FINALLY
        No Operation
    END

*** Keywords ***
Something
    VAR    ${short_variable_name}    value
    VAR    ${loong_but_still_acceptable_variable_name}    value
    VAR    ${some_even_loooooonger_local_variable_name}    value

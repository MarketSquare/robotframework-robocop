*** Variables ***
${SECTION}    value


*** Test Cases ***
Test With VAR
    VAR    ${test_local}    value
    VAR    ${typed_test_local: str}    value
    VAR    ${_ignored}    value
    Log    ${test_local} ${typed_test_local}

Test With Multiline VAR
    VAR
    ...    ${test_multiline}
    ...    value
    Log    ${test_multiline}

Test With Assignment
    ${test_result} =    Set Variable    value
    ${first}    ${second: int}    Set Variable    1    2
    ${typed_result: list} =    Create List    one    two
    ${_ignored} =    Set Variable    value
    Log    ${test_result}


*** Keywords ***
Keyword With VAR
    VAR    ${local}    value
    VAR    ${typed_local: str}    value
    VAR    ${_ignored}    value
    Log    ${local} ${typed_local}

Keyword With Multiline VAR
    VAR
    ...    ${multiline_var}
    ...    value
    VAR
    ...    ${typed_multiline: str}
    ...    value
    Log    ${multiline_var} ${typed_multiline}

Keyword With Assignment
    ${result} =    Set Variable    value
    ${typed_result: list} =    Create List    one    two
    ${_ignored} =    Set Variable    value
    Log    ${result} ${typed_result}

Keyword With Nested Blocks
    IF    $condition
        VAR    ${in_if}    value
    END
    FOR    ${item: str}    IN    a    b
        ${in_for} =    Set Variable    ${item}
    END

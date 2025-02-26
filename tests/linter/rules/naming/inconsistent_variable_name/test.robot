*** Test Cases ***
Consistent variables
    ${variable}    Keyword
    Keyword    ${variable}
    IF    ${variable} < 10
        Log    ${variable}
    END

Inconsistent variables
    ${variable}    Keyword
    Keyword    ${variablE}
    IF    ${var_iable} < 10
        Log    ${varia ble}
    END

*** Keywords ***
Arguments
    [Arguments]    ${consistent}    ${inconsistent}
    Keyword    ${consistent}    ${INconsistent}
    IF    ${i_n_consistenT}    RETURN

Arguments With Defaults
    [Arguments]    ${consistent}    ${inconsistent}='default'
    Keyword    ${consistent}    ${INconsistent}

Embedded ${argument} with ${possible:pattern}
    Keyword    ${ARGUMENT}    ${po_ssible}

Overwritten And Consistent
    ${variable}    Keyword
    ${VARIABLE}    Keyword    ${variable}
    Keyword    ${VARIABLE}

Attribute Access
    [Documentation]    Ignored
    ${variable}    Keyword
    Keyword    ${VARIABLE.attibute}
    Keyword    ${VARIABLE['attibute']}
    Keyword    ${VARIABLE(attibute)}

Nested Variables
    ${variable}    Keyword
    Keyword    ${other_${VARIABLE}}

Assignment Signs
    ${variable}    ${variable2} =    Keyword
    Keyword    ${VARIABLE2}

Set Variable Scope
    ${variable}    Set Variable    value
    Set Test Variable    ${VARIABLE}    ${VARIABLE}  # should report only on second
    BuiltIn.Set Suite Variable    ${VARIABLE}    ${variable}  # should report only on second
    Set Suite Variable    ${VARIABLE}    ${VARIABLE}  # should not report

VAR Syntax
    ${variable}    Set Variable    value
    VAR    ${VARIABLE}    ${VARIABLE}  # should report on second
    VAR    ${variable2}    value    scope=local
    VAR    ${VARIABLE2}    ${variable2}    scope=TEST  # overwritten,  should not report
    VAR    ${VARIABLE2}    Value with ${VARIABLE2}    scope=GLOBAL  # should not report
    VAR    ${VARIABLE3}    Value with inconsistent ${variable2}
    VAR    ${variable}    ${VARIABLE}  # should not report

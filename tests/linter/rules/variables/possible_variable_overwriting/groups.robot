*** Test Cases ***
VAR Syntax
    ${variable_name} =    Set Variable    value
    GROUP
        VAR    ${variableName}    value
        GROUP
            VAR    ${variable name}    value
        END
    END

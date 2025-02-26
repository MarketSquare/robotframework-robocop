*** Test Cases ***
Test with Create keywords
    @{list}    Create List    a   b
    FOR    ${v}    IN    a  b
        &{dict} =    Create Dictionary    key=${v}
    END
    VAR    ${var}


*** Keywords ***
Keyword With Set Variables
    @{list_var}=    Create List    a   b
    TRY
        @{list}    createlist    a   b
    EXCEPT
        &{dict} =    BuiltIn.Create Dictionary    key=${v}
    END
    VAR    ${var}

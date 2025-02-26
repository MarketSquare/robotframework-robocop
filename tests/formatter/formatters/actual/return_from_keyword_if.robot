*** Keywords ***
First
    ${var}    Set Variable    1
    Return From Keyword_If    ${var}==2               ${var}
    FOR    ${variable}  IN  1  2
        Log    ${variable}
    END

With IF
    ${var}    Set Variable    1
    IF    ${var}>0
        IF    ${var}==2
            RETURN    ${var}
        END
    END
    IF    ${var}==2
        RETURN    ${var}
    END

Multiline Statements
    Return From Keyword If  # comment
    ...    ${condition}    ${var}

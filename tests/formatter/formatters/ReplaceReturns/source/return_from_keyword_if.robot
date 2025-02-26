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
        Return From Keyword_If    ${var}==2    ${var}
    END
    Return From Keyword If    ${var}==2
    ...  ${var}

Multiline Statements
    Return From Keyword If  # comment
    ...    ${condition}    ${var}

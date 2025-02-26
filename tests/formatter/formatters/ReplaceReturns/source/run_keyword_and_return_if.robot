*** Keywords ***
First
    ${var}    Set Variable    1
    FOR    ${variable}  IN  1  2
        Run Keyword And Return If    ${var}==2  Keyword 2    ${var}
        Log    ${variable}
    END

With IF
    ${var}    Set Variable    1
    IF    ${var}>0
        Run Keyword And Return If    $var    Some Keyword    ${var}
          ...  1
    END

*** Keywords ***
Run Keyword And Continue On Failure
    [Arguments]    ${keyword}    @{arguments}
    Log    ${keyword}: ${arguments}

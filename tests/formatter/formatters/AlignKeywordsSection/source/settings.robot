*** Keywords ***
Keyword With Settings
    [Documentation]  Docs should be left alone
    ...  even misaligned.
    [Arguments]  ${args}  ${args}    # comment
    [Teardown]  Keyword
    [Timeout]  1min
    Short
    Keyword Arg    ${arg}
    FOR    ${var}   IN RANGE    10
        Keyword Arg    ${arg}
        Other Keyword    ${arg}
    END

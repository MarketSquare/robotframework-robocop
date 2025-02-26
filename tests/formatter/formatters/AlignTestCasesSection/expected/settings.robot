*** Test Cases ***
Keyword With Settings
    [Documentation]  Docs should be left alone
    ...  even misaligned.
    [Tags]                  1234                    1234  # comment
    [Teardown]              Keyword
    [Timeout]               1min
    Short
    Keyword Arg             ${arg}
    FOR    ${var}   IN RANGE    10
        Keyword Arg             ${arg}
        Other Keyword           ${arg}
    END

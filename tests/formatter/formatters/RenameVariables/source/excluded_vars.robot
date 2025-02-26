*** Test Cases ***
Not important variable
    ${_}    ${local}    Keyword    ${global_arg}
    ...
    ...    ${prev_empty}
    FOR    ${_}    IN    @{LIST}
        Log    ${_}
    END
    Multiple Underscores    ${___}    ${ _}    ${_ }    ${ }

*** Keywords ***
Not important variable
    ${_}    ${local}    Keyword    ${global_arg}
    ...
    ...    ${prev_empty}
    FOR    ${_}    IN    @{LIST}
        Log    ${_}
    END
    Multiple Underscores    ${___}    ${ _}    ${_ }    ${ }

Path and line separators
    Load From Path    C${:}/tests${/}file.csv
    Catenate    ${\n}
    ...    sentence
    ...    sentence2

Environment variable
    Log    %{application_port=8080}
    Log    %{env_var}
    Set Test Variable    ${local variable}    %{env variable=string message}
    Log    %{MY_ENV=${default}}
    Log    %{my env=${DEFAULT} with extra}

True and False
    IF    $True
        Log    The truth.
    ELIF    ${False}
        Log    The lie.
    END

Numerical Values
    Log    ${0x1A}
    Log    ${0b0110101}
    Log    ${5}

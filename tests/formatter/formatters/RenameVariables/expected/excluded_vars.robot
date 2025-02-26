*** Test Cases ***
Not important variable
    ${_}    ${local}    Keyword    ${GLOBAL_ARG}
    ...
    ...    ${PREV_EMPTY}
    FOR    ${_}    IN    @{LIST}
        Log    ${_}
    END
    Multiple Underscores    ${_}    ${_}    ${_}    ${_}

*** Keywords ***
Not important variable
    ${_}    ${local}    Keyword    ${GLOBAL_ARG}
    ...
    ...    ${PREV_EMPTY}
    FOR    ${_}    IN    @{LIST}
        Log    ${_}
    END
    Multiple Underscores    ${_}    ${_}    ${_}    ${_}

Path and line separators
    Load From Path    C${:}/tests${/}file.csv
    Catenate    ${\n}
    ...    sentence
    ...    sentence2

Environment variable
    Log    %{APPLICATION_PORT=8080}
    Log    %{ENV_VAR}
    Set Test Variable    ${LOCAL_VARIABLE}    %{ENV_VARIABLE=string message}
    Log    %{MY_ENV=${DEFAULT}}
    Log    %{MY_ENV=${DEFAULT} with extra}

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

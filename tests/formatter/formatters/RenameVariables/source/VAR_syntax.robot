*** Test Cases ***
Long value
    VAR    ${long}
    ...    This value is rather long.
    ...    It has been split to multiple lines.
    ...    Parts will be joined together with a space.

Multiline
    VAR    ${multiline}
    ...    First line.
    ...    Second line.
    ...    Last line.
    ...    separator=\n

Change scope
    # Create a local variable `${local}` with a value `value`.
    VAR    ${local}    value

    # Create a variable that is available throughout the whole suite.
    # Supported scopes are GLOBAL, SUITE, TEST, TASK and LOCAL (default).
    VAR    ${suite}    value    scope=SUITE
    VAR    ${global}    value    scope=GLOBAL
    VAR    ${test}    value    scope=TEST
    VAR    ${task}    value    scope=TASK
    VAR    ${local_default}    value    scope=local

    # Validate created variables.
    Should Be Equal    ${local}    value
    Should Be Equal    ${suite}    value
    Should Be Equal    ${global}    value
    Should Be Equal    ${test}    value
    Should Be Equal    ${task}    value
    IF    $local_default
        Log    Should be lowercase
    ELSE IF    $suite
        Log    Should be uppercase  # Known issue, before VAR
    ELSE IF    $global is None
        Log    Should be uppercase  # Known issue, before VAR
    END
    # if the scope is dynamic, make it global anyway
    VAR    ${variable}    value    scope=${dynamic_scope}
    Log    ${variable}

List
    # Creates a list with three items.
    VAR    @{list}    a    b    c
    Log    ${list}

Dictionary
    # Creates a dictionary with two items.
    VAR    &{dict}    key=value    second=item
    Log    ${dict}

Normal IF
    IF    1 > 0
        VAR    ${x}    true value
    ELSE
        VAR    ${x}    false value
    END
    Log    ${x}

Inline IF
    IF    1 > 0    VAR    ${x}    true value    ELSE    VAR    ${x}    false value
    Log    ${x}

Escaped
    VAR    $variable
    # escaped syntax not supported in definition - variable not defined so scope stays global
    Log    ${variable}

*** Keywords ***
Assignment signs
    VAR    ${variable} =    value
    VAR    ${variable2}=    value
    Log    ${variable}
    Log    ${variable2}

Dynamic Values
    VAR    ${variable}    with ${global} and ${variable}
    VAR    ${variable}    with ${GLOBAL} and ${variable}

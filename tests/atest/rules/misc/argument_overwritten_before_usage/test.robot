*** Variables ***
${VARIABLE}    value


*** Keywords ***
No Arguments
    ${value}    Keyword Call    ${VARIABLE}

Used Arguments
    [Arguments]    ${arg1}    ${arg2}    ${arg3}    ${arg4}    ${arg5}    ${arg6}    ${arg7}
    ${value}    Set Variable    ${a_rg1}
    IF    $arg5 != '${arg6}' and $arg7
        Log    Mixed syntax
    END
    Set Global Variable    \${arg4}    value

Not Used Arguments
    [Arguments]    ${arg1}    ${arg2}
    ${value}    Set Variable    ${arg 1}

Overwritten Argument
    [Arguments]    ${arg1}    ${overwritten1}    ${overwritten2}    ${overwritten3}    ${overwritten_but_used}
    ${overwritten1}    Set Variable    ${arg1}
    ${overwritten2}    Set Variable    ${arg1}
    ${overwritten_but_used}    Keyword    String with ${overwritten_but_used}
    Keyword Call    ${overwritten1}  # used, but by overwritten
    Keyword Call    ${overwritten2}  # used, but by overwritten
    FOR    ${overwritten3}    IN    @{arg1}
        Log    ${overwritten3}
    END

Used In For
    [Arguments]    ${for_arg}
    FOR    ${item}    IN    @{for_arg}
        No Operation
    END

Overwritten In Try As
    [Arguments]    ${error}    ${used}
    TRY
        Do Stuff
    EXCEPT    Error    AS    ${error}
        Log    ${error}
    FINALLY
        Keyword    ${used}
    END

Errors In Arguments
    [Arguments]    ${argument} = value
    Log    ${argument}

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

Overwritten In Inline IF
    [Arguments]    ${arg}
    ${arg}    IF  ${CONDITION}  Replace String  ${arg}  TAG  ${CONDITION_TAG}

Overwritten In Inline IF ELSE
    [Arguments]    ${arg}
    ${arg}    IF  ${CONDITION}  Do Nothing  ELSE  Replace String  ${arg}  TAG  ${CONDITION_TAG}

Overwritten In Inline IF ELSE IF
    [Arguments]    ${arg}
    ${arg}    IF  ${CONDITION}  Do Nothing  ELSE IF  ${OTHER}  Replace String  ${arg}  TAG  ${CONDITION_TAG}

Overwritten In Inline IF - Just Variable
    [Documentation]    Should not raise anything - it is not argument
    ${variable}    Set Variable    default value
    ${variable}    IF  ${CONDITION}  Replace String  ${variable}  TAG  ${CONDITION_TAG}

Overwritten in VAR
    [Arguments]    ${arg1}    ${overwritten1}    ${overwritten2}    ${overwritten_but_used}
    VAR    ${overwritten1}    ${arg1}
    VAR    ${overwritten2}    ${arg1}
    VAR    ${overwritten_but_used}    String with ${overwritten_but_used}
    Keyword Call    ${overwritten1}  # used, but overwritten before
    Keyword Call    ${overwritten2}  # used, but overwritten before

Argument Conditionally Overwritten
    [Documentation]    It should be ignored as it's not always overwritten.
    [Arguments]    ${to print}    ${another arg}
    IF    ${another arg} != "KEEP"
        VAR    ${to print}    "overwrite"
    END
    Log To Console    ${to print}

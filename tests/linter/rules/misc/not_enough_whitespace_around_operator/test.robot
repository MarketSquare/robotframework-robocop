*** Test Cases ***
If condition
    IF    ${variable}==5
        Log    ${variable}
    ELSE IF    ${variable} !=5
        Log    ${variable}
    ELSE IF    ${variable}> 5
        Log    ${variable}
    END
    IF    ${variable} == 5
        Log    ${variable}
    END

Inline if
    IF    ${counter}<=${LIMIT}    Log    ${counter}
    ${assign}    IF    ${x}>${y}    Set Variable    big    ELSE    Set Variable    small

While condition
    WHILE    ${counter}>=${LIMIT}
        ${counter}    Evaluate    ${counter} + 1
    END
    WHILE    ${counter} < ${LIMIT}
        ${counter}    Evaluate    ${counter} + 1
    END

Chained condition
    IF    5<${a}<10
        Log    ${a}
    END

Keywords with conditions
    Should Be True    ${left}!=${right}
    Skip If    ${status}==${FALSE}
    Pass Execution If    ${left} > ${right}    message
    Set Variable If    ${x}<${y}    small    ${x} > ${y}    big

Not a condition
    Should Be True    ${left} == ${right}
    Log    ${left}==${right}
    IF    ${text} == "a<b"
        Log    ${text}
    END

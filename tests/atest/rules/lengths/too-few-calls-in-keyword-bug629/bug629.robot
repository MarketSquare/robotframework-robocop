*** Settings ***
Documentation      Test rule too-few-calls-in-keyword

Resource    ../../misc/if-can-be-merged/test.robot

*** Test Cases ***
My Test Case
    No Operation


*** Keywords ***
Keyword With Some Logic
    [Arguments]        ${value}
    IF    ${value} == ${A}
        RETURN    ${1}
    ELSE IF    ${value} == ${B}
        RETURN    ${2}
    ELSE IF    ${value} == ${C}
        RETURN    ${3}
    ELSE IF    ${value} == ${D}
        RETURN    ${4}
    ELSE
        Log    Unexpected value ${value}.    console=yes
        No Operation
        RETURN    ${0}
    END

Keyword Call Only In ELSE
    IF    $condition
        No Operation
    ELSE
        No Operation
    END

Inline IF
    IF    $flag    Keyword    ELSE IF    not $flag    Keyword2    ${arg}

TRY EXCEPT
    TRY
        No Operation
    EXCEPT    *
        No Operation
    FINALLY
        RETURN    ${1}
    END

WHILE
    WHILE    ${x}
        IF    ${x} % 2 == 0    CONTINUE
        BREAK
    END

*** Settings ***
Documentation      Test rule too-few-calls-in-keyword


*** Test Cases ***
Test With Some Logic
    IF    ${value} == ${A}
        Log    ${1}
    ELSE IF    ${value} == ${B}
        Log    ${2}
    ELSE IF    ${value} == ${C}
        Log    ${3}
    ELSE IF    ${value} == ${D}
        Log    ${4}
    ELSE
        Log    Unexpected value ${value}.    console=yes
        No Operation
        Log    ${0}
    END

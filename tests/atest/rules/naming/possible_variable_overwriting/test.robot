*** Test Cases ***
Test With Overwritten Variables
    ${my_var}       Set Variable    1
    ${my_var}       Set Variable    2
    ${MY VAR}       Set Variable    2
    ${myVar}        Set Variable    3
    ${another_var}  Set Variable    4
    ${MYVAR}        Set Variable    5
    ${M Y V A R}    Set Variable    6
    ${mYvAr}        Some Keyword    123

Test With Template
    [Template]  Templated Keyword
    10     arg2
    20     arg3
    -30    arg4
#comment

*** Keywords ***
Keyword With For Loops
    FOR  ${val}  IN  @{some_list}
        ${VAL}    Some Variable    1
    END
    FOR  ${my_var}  IN  @{my_list}
        Keyword With Multiline
        ...  ${myVar}
        FOR  ${this_var}  IN  @{this_list}
            My Keyword    ${myVar}
            ${this var}     This Keyword   ${MY_VAR}
        END
        ${unique}  ${myVar}    Keyword
        FOR  ${this_var}  IN  @{this_list}
            My Keyword    ${myVar}
            ${this var}     This Keyword   ${MY_VAR}
        END
    END

Keyword With If Conditions
    ${v a l}    Some Keyword
    IF  ${val}
        ${VAL}    Set Variable    1
    END
    IF  ${my_val} == ${True}
        ${my val}    Change To False
    END
    ${MY_VAL}    Change To True
    IF  ${some_val}
        ${some val}  ${another val}  ${val}  Return Three Values
        IF  ${another_val}
            ${some val}  ${another val}  ${val}  Return Three Values
        END
    END

Keyword With Overwritten Variables
    [Arguments]     ${my_var}
    ${someVar}      Set Variable    1
    ${SOME_VAR}     Set Variable    2
    ${myvar}        Set Variable    3
    ${myvar}        Set Variable    4
    ${somevar}      ${some var}     Return Two Values

Keyword With Different Types Of Variables
    [Arguments]     ${simple_var}
    ${simple_var}   Set Variable        1
    ${simpleVar}    Set Variable        2
    @{SIMPLE_VAR}   Create List         1    2    3
    &{SIMPLE_VAR}   Create Dictionary   a=1  b=2  c=3

Argument With Default Value
    [Arguments]     ${variable}='default'
    ${VARIABLE}    Keyword  # possible overwriting

Embedded ${variable} with ${possible:pattern}
    ${other}    Keyword    ${variable}
    ${VARIABLE}   Possible Overwriting
    ${poss_ible}   IF    $cond    RETURN

IF Assignment
    ${initial}    IF    ${condition} > 0    Keyword
    ${_initiaL}    Possible Overwriting

Assignment Sign
    ${variable}    Keyword
    ${VARiable} =    Keyword

Keyword With Kwargs
    [Arguments]    ${argument}    &{keyword_args}
    ${keyword_args}    Create Dictionary   key=${FLAG}    &{keyword_args}

Keyword With Possible Overwritten Kwargs
    [Arguments]    ${argument}    &{keyword_args}
    ${keywordArgs}    Create Dictionary    &{keyword_args}

Assignment Sign But Not Overwritten
    ${v} =    No Operation
    Log    ${v}
    ${v} =    No Operation
    Log    ${v}

Item Assignment
    ${variable}    Create Dictionary
    ${VARIABLE}[item]    Set Variable    value

VAR Syntax
    ${variable_name} =    Set Variable    value
    VAR    ${variableName}    value
    VAR    ${variable name}    value    scope=GLOBAL
    VAR    ${variable namE}=    value    scope=local
    VAR    ${variable_name}    Value with ${Variable_Name}    scope=SUITE

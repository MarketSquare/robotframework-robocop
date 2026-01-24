*** Keywords ***
Set without typing
    Set Local Variable    ${variable}    value
    Set Suite Variable    ${variable}    value
    Set Test Variable    ${variable}    value
    Set Task Variable    ${variable}    value
    Set Global Variable    ${variable}    value

Set with typing
    Set Local Variable    ${variable: int}    value
    Set Suite Variable    ${variable: str}    value
    Set Test Variable    ${variable: list[str]}    value
    Set Task Variable    ${variable: int}    value
    Set Global Variable    ${variable: int}    value

Missing name
    Set Local Variable
    Set Suite Variable
    Set Test Variable
    Set Task Variable
    Set Global Variable

VAR
    VAR    ${variable: int}    value
    VAR    ${variable: str}    value
    VAR    ${variable: list[str]}    value
    VAR    ${variable: int}    value
    VAR    ${variable: int}    value

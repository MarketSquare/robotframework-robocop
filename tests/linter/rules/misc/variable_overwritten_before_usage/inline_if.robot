*** Keywords ***
Overwritten In Inline IF
    ${variable}    Set Variable    default value
    ${variable}    IF  ${CONDITION}  Replace String  ${variable}  TAG  ${CONDITION_TAG}

Overwritten In Inline IF ELSE
    ${variable}    Set Variable    default value
    ${variable}    IF  ${CONDITION}  Do Nothing  ELSE  Replace String  ${variable}  TAG  ${CONDITION_TAG}

Overwritten In Inline IF ELSE IF
    ${variable}    Set Variable    default value
    ${variable}    IF  ${CONDITION}  Do Nothing  ELSE IF  ${OTHER}  Replace String  ${variable}  TAG  ${CONDITION_TAG}

Overwritten In Inline IF - Arguments
    [Documentation]    Should not raise anything - it is argument.
    [Arguments]    ${arg}
    ${arg}    IF  ${CONDITION}  Replace String  ${arg}  TAG  ${CONDITION_TAG}

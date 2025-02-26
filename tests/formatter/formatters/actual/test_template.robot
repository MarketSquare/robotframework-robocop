*** Settings ***
Test Template    ${GLOBAL_KEYWORD_NAME}


*** Test Cases ***
Template with for loop
    FOR    ${item}    IN    @{ITE_MS}
        ${item}    2nd arg
    END
    FOR    ${index}    IN RANGE    42
        1st arg    ${index}   ${GLOBAL}
    END

Test Name   ${ARG}    ${ARG2}

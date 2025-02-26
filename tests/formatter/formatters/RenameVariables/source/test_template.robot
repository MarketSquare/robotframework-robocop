*** Settings ***
Test Template    ${global keyword name}


*** Test Cases ***
Template with for loop
    FOR    ${item}    IN    @{ITEMs}
        ${item}    2nd arg
    END
    FOR    ${index}    IN RANGE    42
        1st arg    ${index}   ${global}
    END

Test Name   ${arg}    ${arg2}

*** Settings ***
Test Template    Dummy

*** Test Cases ***    foo    bar
Template with for loop
    FOR    ${item}    IN    @{ITEMS}
        ${item}    2nd arg
    END
    FOR    ${index}    IN RANGE    42
        1st arg    ${index}
    END

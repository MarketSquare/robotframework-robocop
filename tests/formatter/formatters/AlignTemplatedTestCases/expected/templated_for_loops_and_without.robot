*** Settings ***
Test Template    Dummy

*** Test Cases ***
Template with for loop
    FOR    ${item}    IN    @{ITEMS}
                            ${item}     2nd arg
    END
    FOR    ${index}    IN RANGE    42
                            1st arg     ${index}
    END
                            test        ${arg}

# some comment
test1                       hi          hello
test2 long test name        asdfasdf    asdsdfgsdfg
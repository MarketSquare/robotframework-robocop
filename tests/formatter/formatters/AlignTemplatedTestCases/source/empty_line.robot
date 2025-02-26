*** Settings ***
Test Template       bar

*** Test Cases ***      baz         qux
test1
                        hi          hello
test2 long test name
                        asdfasdf    asdsdfgsdfg

*** Keywords ***
bar
    [Arguments]    ${baz}    ${qux}
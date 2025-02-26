*** Settings ***
Test Template       bar

*** Test Cases ***    baz    qux
# some comment
test1    hi    hello
test2 long test name    asdfasdf    asdsdfgsdfg
    bar1  bar2
# some comment

*** Keywords ***
bar
    [Arguments]    ${baz}    ${qux}

*** Settings ***
Test Template       bar

*** Test Cases ***
# some comment
test1    hi    hello  # robotidy: off
# robotidy: off
test2 long test name    asdfasdf    asdsdfgsdfg
    bar1  bar2
# some comment

*** Keywords ***
bar
    [Arguments]    ${baz}    ${qux}

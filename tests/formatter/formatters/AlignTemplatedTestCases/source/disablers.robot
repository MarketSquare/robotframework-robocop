*** Settings ***
Test Template       bar

*** Test Cases ***
# some comment
test1    hi    hello  # robocop: fmt: off
# robocop: fmt: off
test2 long test name    asdfasdf    asdsdfgsdfg
    bar1  bar2
# some comment

*** Keywords ***
bar
    [Arguments]    ${baz}    ${qux}

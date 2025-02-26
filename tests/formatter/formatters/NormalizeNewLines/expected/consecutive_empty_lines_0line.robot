*** Settings ***
Resource    resource.robot
Default Tags    tag
Documentation    doc


*** Test Cases ***
Test Capitalized
    Pass Execution

test not capitalized
    Pass Execution

TEST UPPERCASE
    Pass Execution

Test with first letter capitalized
    Pass Execution
#  no test case name
    Log To Console  hello


*** Keywords ***
Keyword
    Empty Line Before
    One Line
    Two Empty Lines

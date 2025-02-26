*** Settings ***
Task Setup      Some Keyword
Test Teardown   Some Keyword
Task Template   Some Keyword
Test Timeout    100
Task Tags       tag
Documentation   some docs


*** Variables ***
${variable}    value



*** Tasks ***
Some Task
    No Operation

*** Keywords ***
Some Keyword
    No Operation

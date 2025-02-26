*** Settings ***
Task Setup      Some Keyword
Test Teardown   Some Keyword
Task Template   Some Keyword
Test Timeout    100
Task Tags       tag
Documentation   some docs


*** Variables ***
${variable}    value


*** Test Cases ***
Some Task
    No Operation

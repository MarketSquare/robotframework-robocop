*** Settings ***
Library  SomeLib
# robocop: on

*** Test Cases ***
Test 1  # robocop: off=LEN08
    Keyword1

*** Keywords ***
Keyword1  # robocop: off=line-too-long
    Log  1  # robocop: off=some-rule
    No Operation  # noqa

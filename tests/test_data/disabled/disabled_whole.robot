# robocop: disable
*** Settings ***
Library  SomeLib

*** Test Cases ***
Test 1
    Keyword1

*** Keywords ***
Keyword1  # robocop: disable=somerule
    Log  1
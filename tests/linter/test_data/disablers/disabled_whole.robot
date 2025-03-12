# robocop: off
*** Settings ***
Library  SomeLib

*** Test Cases ***
Test 1
    Keyword1

*** Keywords ***
Keyword1  # robocop: off=somerule
    Log  1

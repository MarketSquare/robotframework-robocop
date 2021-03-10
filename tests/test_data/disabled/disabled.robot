# robocop: disable
*** Settings ***
Library  SomeLib
# robocop: enable

*** Test Cases ***
Test 1  # robocop: disable=1010
    Keyword1

*** Keywords ***
Keyword1  # robocop: disable=somerule
    Log  1  # robocop: disable=test-rule
    No Operation  # noqa
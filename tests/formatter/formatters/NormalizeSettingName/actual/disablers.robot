*** Settings ***
Library  # robocop: fmt: off
Documentation    This is example documentation
...              which is also multiline  # robocop: fmt: off
# robocop: fmt: off
Force Tags  tag1     tag2
Test Template  Keyword


*** Test Cases ***
Test
    [Setup]    Keyword2    # robocop: fmt: off
    No Operation
    [Teardown]    # robocop: fmt: off


*** Keywords ***  # robocop: fmt: off
Keyword
    [Arguments]    ${arg}
    Pass

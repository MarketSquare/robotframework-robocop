# robocop: fmt: off
*** Settings ***


# robocop: fmt: on
*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    One More
    # robocop: fmt: off


*** Keywords ***
# This section is considered to be empty.
# robocop: fmt: off


*** Variables ***  # robocop: fmt: off

*** Comments ***
# robocop: off=all

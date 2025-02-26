# robotidy: off
*** Settings ***


# robotidy: on
*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    One More
    # robotidy: off


*** Keywords ***
# This section is considered to be empty.
# robotidy: off


*** Variables ***  # robotidy: off

*** Comments ***
# robocop: disable=all

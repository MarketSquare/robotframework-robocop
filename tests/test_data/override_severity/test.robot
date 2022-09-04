*** Settings ***
Documentation    Testing Robocop
Force Tags       comeANDgo    # Evoke rule 0602 with severity I


*** Test Cases ***
Log Something
    # Missing [Documentation] evokes rule 0202 with severity W
    Log To Console    \nNice day today
    No Operation

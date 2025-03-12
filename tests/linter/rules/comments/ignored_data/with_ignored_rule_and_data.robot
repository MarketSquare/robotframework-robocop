# robocop: off=1001
${var}    10    # This should throw a warning.
${var}    20    # This is not good but one warning is enough.
*** Settings ***
Documentation    Doc


*** Test Cases ***
First Test Case
    [Documentation]    Doc
    No Operation

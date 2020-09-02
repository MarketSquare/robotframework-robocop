*** Settings ***
Documentation  doc
Library StatusLib


*** Variables ***
${var} 2


*** Test Cases ***
Test
    [Documentation] doc
    Keyword
    [Teardown] Teardown
*** Settings ***
Library   String
Documentation   test


*** Variables ***
  ${MY VAR}  10


*** Test Cases ***
Test
    [Documentation]  doc
    Log  ${MY VAR}

*** Settings ***
Library   String
Documentation   test


*** Variables ***
 ${MY VAR}  10
  ${MY VAR1}  10
   ${MY VAR2}  10
    ${MY VAR3}  10
${GOLD VAR}  10


*** Test Cases ***
Test
    [Documentation]  doc
    Log  ${MY VAR}

*** Settings ***
Resource    common.resource
Resource    other.resource

*** Variables ***
${BROWSER}    edge
${LOCAL}    value

*** Test Cases ***
Test
    Log    ${BROWSER}
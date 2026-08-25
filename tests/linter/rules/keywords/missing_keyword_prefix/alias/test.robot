*** Settings ***
Library     Collections    AS    Coll

*** Test Cases ***
Test
    Append To List    ${list}    item
    Coll.Append To List    ${list}    item

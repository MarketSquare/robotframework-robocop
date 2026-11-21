*** Settings ***
Library     LibOne.py
Library     LibTwo.py
Resource    order.resource
Suite Setup    Use Second Implementation


*** Test Cases ***
Library Conflict
    Click Thing

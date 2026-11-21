*** Settings ***
Library     LibOne.py
Library     LibTwo.py
Resource    first.resource
Resource    second.resource
Resource    flows.resource


*** Test Cases ***
Library Conflict
    Set Library Search Order    LibTwo    second
    Click Thing

Resource Conflict
    Open Page

Later Test In The Same Suite
    Click Thing
    Open Page Flow

*** Settings ***
Resource    first.resource
Resource    does_not_exist.resource

*** Test Cases ***
Test
    Keyword From First

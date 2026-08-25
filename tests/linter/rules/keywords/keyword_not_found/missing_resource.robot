*** Settings ***
Resource    does_not_exist.resource

*** Test Cases ***
Test
    Keyword From Resource That Was Not Found

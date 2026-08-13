*** Settings ***
Resource    resources/keywords.resource
Resource    resources/unused.resource
Resource    resources/variables.resource
Resource    resources/only_imports.resource

*** Test Cases ***
Test
    Used Keyword
    Log    ${SHARED_VAR}
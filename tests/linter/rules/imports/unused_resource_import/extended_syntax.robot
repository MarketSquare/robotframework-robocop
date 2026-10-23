*** Settings ***
Resource    resources/dict_variables.resource
Resource    resources/object_variables.resource

*** Test Cases ***
Test
    Log    ${MY_DICT['key']}
    Log    ${MY_OBJECT.upper()}


*** Settings ***
Documentation    This is suite doc


*** Test Cases ***
Test
    [Documentation]   doc
    Keyword


*** Keywords ***
Keyword With Argument
    [Documentation]   Gold test
    [Arguments]    ${element}    @{items}   ${key 1}=${1}
    Log  ${element.attr}
    Log  ${items[0]}
    Log  ${key 1}

Keyword With Argument But Not Used
    [Documentation]   doc
    [Arguments]    ${element}    @{items}   ${key 1}=${1}
    Log  ${var}

*** Settings ***
Documentation   test


*** Test Cases ***
Test 1
    [Documentation]    doc
    No Operation


*** Keywords ***
Correct Keyword
    [Documentation]  doc
    [Arguments]    ${argument_1}
    ...            ${argument_2}
    Log Many    ${argument_1}    ${argument_2}

Another Correct Keyword
    [Documentation]  doc
    [Arguments]    ${optional_argument}=value
    Log    ${optional_argument}

Keyword With First Arg In New Line
    [Documentation]  doc
    [Arguments]
    ...     ${optional_argument}=value
    Log    ${optional_argument}

Another Keyword With First Arg In New Line
    [Documentation]  doc
    [Arguments]
    ...     ${some_argument}
    Log    ${some_argument}

Free Named Only
    [Documentation]  doc
    [Arguments]
    ...    &{named}
    Log Many    &{named}

Positional And Free Named
    [Documentation]  doc
    [Arguments]
    ...    ${required}
    ...    &{extra}
    Log Many    ${required}    &{extra}

Run Program
    [Documentation]  doc
    [Arguments]
    ...    @{args}
    ...    &{config}
    No Operation

With Varargs
    [Documentation]  doc
    [Arguments]
    ...    @{varargs}
    ...    ${named}
    Log Many    @{varargs}    ${named}

Without Varargs
    [Documentation]  doc
    [Arguments]
    ...    @{}
    ...    ${first}
    ...    ${second}
    Log Many    ${first}    ${second}

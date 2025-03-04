*** Settings ***
Default Tags  tag
... tag2

Force Tags  tag
..    tag2

  Library  Collections

*** Test Case ***
    [Invalid]  arg
    [Arguments]  ${arg}
    [Return]    ${value}

*** Keywords ***
    [Invalid]    arg
    [Setup]    ${arg}
    [Template]    Keyword
    [Metadata]    Not valid.
    [Doc Umentation]

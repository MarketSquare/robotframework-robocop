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
    [Argument]   ${value}
    [Invalid]    arg
    [Setup]    ${arg}
    [Template]    Keyword
    [Doc Umentation]

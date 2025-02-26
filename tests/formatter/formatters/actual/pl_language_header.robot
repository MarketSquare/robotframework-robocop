language: pl

*** Settings ***
Library    python.py
Documentation    This is doc

Suite Teardown    Keyword

Task Tags    tag


*** Variables ***
${VAR}    ${TRUE}


*** Test Cases ***
Pierwszy test
    [Setup]
    [Tags]
    Słowo kluczowe

Dokumentacja
    [Documentation]    This is doc
    No Operation

*** Keywords ***
Keyword
    [Arguments]    ${arg}
    IF    $condition
        Log    ${arg}
    ELSE
        BREAK
    END

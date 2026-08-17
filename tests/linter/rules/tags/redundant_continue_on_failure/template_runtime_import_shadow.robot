*** Settings ***
Test Template    Run Keyword


*** Test Cases ***
Import shadow from template
    Import Resource    ${CURDIR}${/}runtime_import_shadow.resource

Wrapper after template import
    [Template]    NONE
    [Tags]    robot:continue-on-failure
    Run Keyword And Continue On Failure    Fail    Unqualified wrapper must stay shadowed
    BuiltIn.Run Keyword And Continue On Failure    No Operation

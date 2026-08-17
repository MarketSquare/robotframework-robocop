*** Settings ***
Suite Setup    Import Resource    ${CURDIR}${/}runtime_import_shadow.resource


*** Test Cases ***
Runtime imported shadows
    [Tags]    robot:continue-on-failure
    Run Keyword And Continue On Failure    Fail    Unqualified wrapper must stay shadowed
    BuiltIn.Run Keyword And Continue On Failure    No Operation

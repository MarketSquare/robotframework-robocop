*** Settings ***
Suite Setup    Run\ Keyword    BuiltIn.Import\ Resource    ${CURDIR}${/}runtime_import_shadow.resource


*** Test Cases ***
Nested escaped runtime imported shadow
    [Tags]    robot:continue-on-failure
    Run Keyword And Continue On Failure    Fail    Unqualified wrapper must stay shadowed
    BuiltIn.Run Keyword And Continue On Failure    No Operation

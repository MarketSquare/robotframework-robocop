*** Settings ***
Suite Setup    Run Keyword    ${IMPORT_RESOURCE}    ${CURDIR}${/}runtime_import_shadow.resource


*** Variables ***
${IMPORT_RESOURCE}    Import Resource


*** Test Cases ***
Dynamic runtime imported shadow
    [Tags]    robot:continue-on-failure
    Run Keyword And Continue On Failure    Fail    Unqualified wrapper must stay shadowed
    BuiltIn.Run Keyword And Continue On Failure    No Operation

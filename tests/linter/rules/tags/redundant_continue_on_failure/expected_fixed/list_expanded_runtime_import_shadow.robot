*** Settings ***
Suite Setup    Run Keyword If    @{CONDITION_AND_IMPORT}


*** Variables ***
@{CONDITION_AND_IMPORT}    ${TRUE}    Import Resource    ${CURDIR}${/}runtime_import_shadow.resource


*** Test Cases ***
List expanded runtime imported shadow
    [Tags]    robot:continue-on-failure
    Run Keyword And Continue On Failure    Fail    Unqualified wrapper must stay shadowed
    BuiltIn.Run Keyword And Continue On Failure    No Operation

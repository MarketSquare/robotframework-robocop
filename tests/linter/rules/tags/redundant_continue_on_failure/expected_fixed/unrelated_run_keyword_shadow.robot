*** Settings ***
Suite Setup    Run Keyword    Import Resource    ${CURDIR}${/}runtime_import_shadow.resource


*** Test Cases ***
Runtime import under unrelated run keyword
    [Tags]    robot:continue-on-failure
    BuiltIn.Run Keyword And Continue On Failure    No Operation


*** Keywords ***
Run Keyword If
    [Arguments]    @{arguments}
    Log    ${arguments}

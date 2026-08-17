*** Settings ***
Suite Setup    Import Shadow With Call Method


*** Variables ***
${RESOURCE_PATH}    ${{r'${CURDIR}'.replace(chr(92), '/') + '/runtime_import_shadow.resource'}}


*** Test Cases ***
Call Method runtime imported shadow
    [Tags]    robot:continue-on-failure
    Run Keyword And Continue On Failure    Fail    Unqualified wrapper must stay shadowed
    BuiltIn.Run Keyword And Continue On Failure    No Operation


*** Keywords ***
Import Shadow With Call Method
    ${builtin}=    Get Library Instance    BuiltIn
    Call Method
    ...    ${builtin}
    ...    import_resource
    ...    ${RESOURCE_PATH}

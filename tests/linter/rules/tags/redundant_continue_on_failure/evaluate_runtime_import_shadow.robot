*** Settings ***
Suite Setup    Import Shadow With Evaluate


*** Variables ***
${RESOURCE_PATH}    ${{r'${CURDIR}'.replace(chr(92), '/') + '/runtime_import_shadow.resource'}}


*** Test Cases ***
Evaluate runtime imported shadow
    [Tags]    robot:continue-on-failure
    Run Keyword And Continue On Failure    Fail    Unqualified wrapper must stay shadowed
    BuiltIn.Run Keyword And Continue On Failure    No Operation


*** Keywords ***
Import Shadow With Evaluate
    Evaluate
    ...    __import__('robot.libraries.BuiltIn', fromlist=['BuiltIn']).BuiltIn().import_resource(r'${RESOURCE_PATH}')

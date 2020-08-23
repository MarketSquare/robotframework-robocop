*** Settings ***
Documentation  dummy
Force Tags  Sometag  in_both_places
Default Tags  defaulttag

*** Test Cases ***
Test1
    [Documentation]  dummy
    [Tags]  Sometag  smth  in_both_places

Test2
    [Documentation]  dummy
    [Tags]  smth  in_both_places

Test3
    [Documentation]  dummy
    [Tags]  other_tag  smth  in_both_places

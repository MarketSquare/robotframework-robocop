*** Settings ***
Default Tags    tag1    tag2    tag4    tag5    # comment


*** Keywords ***
Keyword
    [Tags]    tag2    tag3    tag4    tag5    # comment1    # comment2


*** Test Cases ***
Test
    [Tags]    neednormalization_now    also_need_normalization    tag    # Tell some    # interesting story    # about those tags

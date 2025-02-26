*** Settings ***
Default Tags        tag1    tag2    tag1    tag4    tag4    tag5    tag5    # comment


*** Keywords ***
Keyword
    [Tags]
    ...    tag2
    ...    tag3    # comment1
    ...    tag4
    ...    tag4
    ...    tag5    # comment2
    ...    tag5


*** Test Cases ***
Test
    [Tags]    neednormalization_now    # Tell some
    ...    also_need_normalization     # interesting story
    ...     tag                        # about those tags

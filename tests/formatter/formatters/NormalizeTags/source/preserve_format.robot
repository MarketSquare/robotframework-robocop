*** Settings ***
Default Tags        tag1    Tag2    TAG1    tag4    tag4    tag5    TAG5    # comment


*** Keywords ***
Keyword
    [Tags]
    ...    Tag2
    ...    TAG3    # comment1
    ...    tag4
    ...    tag4
    ...    tag5    # comment2
    ...    TAG5


*** Test Cases ***
Test
    [Tags]    NeedNormalization_Now    # Tell some
    ...    also_need_Normalization     # interesting story
    ...     TAG                        # about those tags

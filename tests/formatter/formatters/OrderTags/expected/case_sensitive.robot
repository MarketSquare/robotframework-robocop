*** Settings ***
Documentation       OrderTags acceptance tests
Force Tags    forced_tag_1    forced_tag_2    forced_tag_Ab    forced_tag_Bb    forced_tag_aa    forced_tag_ba
Default Tags    default_tag_1    default_tag_2    default_tag_Ab    default_tag_Bb    default_tag_aa    default_tag_ba    # comment

*** Test Cases ***
No tags
    No Operation

Tags Upper Lower
    [Tags]    Ab    Bb    Ca    Cb    aa    ba
    My Keyword

One Tag
    [Tags]    one_tag
    One Tag Keyword

Multiline tags
    [Tags]    TAG3    TAG5    Tag2    tag1    tag3    tag4    tag4    # comment    # comment2
    No Operation

*** Keywords ***
My Keyword
    [Tags]    Ab    Bb    Ca    Cb    aa    ba    # comment
    No Operation

One Tag Keyword
    [Tags]    one_tag
    No Operation
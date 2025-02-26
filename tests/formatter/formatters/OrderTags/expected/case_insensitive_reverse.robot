*** Settings ***
Documentation       OrderTags acceptance tests
Force Tags    forced_tag_Bb    forced_tag_ba    forced_tag_Ab    forced_tag_aa    forced_tag_2    forced_tag_1
Default Tags    default_tag_Bb    default_tag_ba    default_tag_Ab    default_tag_aa    default_tag_2    default_tag_1    # comment

*** Test Cases ***
No tags
    No Operation

Tags Upper Lower
    [Tags]    Cb    Ca    Bb    ba    Ab    aa
    My Keyword

One Tag
    [Tags]    one_tag
    One Tag Keyword

Multiline tags
    [Tags]    TAG5    tag4    tag4    tag3    TAG3    Tag2    tag1    # comment    # comment2
    No Operation

*** Keywords ***
My Keyword
    [Tags]    Cb    Ca    Bb    ba    Ab    aa    # comment
    No Operation

One Tag Keyword
    [Tags]    one_tag
    No Operation
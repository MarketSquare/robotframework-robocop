*** Settings ***
Documentation       OrderTags acceptance tests
Force Tags    forced_tag_ba    forced_tag_aa    forced_tag_Bb    forced_tag_Ab    forced_tag_2    forced_tag_1
Default Tags    default_tag_ba    default_tag_aa    default_tag_Bb    default_tag_Ab    default_tag_2    default_tag_1    # comment

*** Test Cases ***
No tags
    No Operation

Tags Upper Lower
    [Tags]    ba    aa    Cb    Ca    Bb    Ab
    My Keyword

One Tag
    [Tags]    one_tag
    One Tag Keyword

Multiline tags
    [Tags]    tag4    tag4    tag3    tag1    Tag2    TAG5    TAG3    # comment    # comment2
    No Operation

*** Keywords ***
My Keyword
    [Tags]    ba    aa    Cb    Ca    Bb    Ab    # comment
    No Operation

One Tag Keyword
    [Tags]    one_tag
    No Operation
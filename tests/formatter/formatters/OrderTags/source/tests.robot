*** Settings ***
Documentation       OrderTags acceptance tests
Force Tags    forced_tag_1    forced_tag_aa     forced_tag_2    forced_tag_Ab    forced_tag_Bb    forced_tag_ba
Default Tags    default_tag_1    default_tag_aa    default_tag_2    default_tag_Ab    default_tag_Bb    default_tag_ba  # comment

*** Test Cases ***
No tags
    No Operation

Tags Upper Lower
    [Tags]    ba    Ab    Bb    Ca    Cb    aa
    My Keyword

One Tag
    [Tags]    one_tag
    One Tag Keyword

Multiline tags
    [Tags]    tag1
    ...    Tag2
    ...    TAG5
    ...    tag4  # comment
    ...    tag4
    ...    tag3
    ...    TAG3  # comment2
    No Operation

*** Keywords ***
My Keyword
    [Tags]    ba    Ab    Bb    Ca    Cb    aa  # comment
    No Operation

One Tag Keyword
    [Tags]    one_tag
    No Operation
*** Settings ***
Documentation       OrderTags acceptance tests
Force Tags    Tag1    tag1    tag2    tag2    tag3    tag4
Default Tags    Tag1    tag1    tag2    tag2    tag3    tag4

*** Test Cases ***
No tags
    Keyword no tags

Different cases
    [Tags]    Tag1    tag1    TAG1    other_tag
    Keyword different cases

Same cases
    [Tags]    tag2    tag2    other_tag
    Keyword same cases

Not duplicates
    [Tags]    tag3    tag4
    Keyword not duplicates

One Tag
    [Tags]    tag5
    One Tag Keyword

*** Keywords ***
Keyword no tags
    No Operation

Keyword same cases
    [Tags]    tag2    tag2    other_tag
    No Operation

Keyword different cases
    [Tags]    Tag1    tag1    TAG1    other_tag
    No Operation

Keyword not duplicates
    [Tags]    tag3    tag4
    No Operation

One Tag Keyword
    [Tags]    tag5
    No Operation
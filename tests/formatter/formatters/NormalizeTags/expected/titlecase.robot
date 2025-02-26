*** Settings ***
Documentation       OrderTags acceptance tests
Force Tags    Tag1    Tag2    Tag3    Tag4    Tag5    # comment
Default Tags    Tag1    Tag2    Tag3    Tag4    Tag5    # comment

*** Test Cases ***
No tags
    Keyword no tags

Normalize case
    [Tags]    Foo_Bar_Baz_A    Foo_Bar_Baz_B    Foo_Bar_Baz_C    Foobarbazd    Foobarbaze    Foobarbazf    Foo Bar Baz G    Foo Bar Baz H    Foo Bar Baz I
    Keyword normalize case

Deduplicate
    [Tags]    Tag_A    Tag_B    Tag_C
    Keyword deduplicate

Deduplicate and normalize case
    [Tags]    Foo_Bar_Baz_A    Foo_Bar_Baz_B    Foo_Bar_Baz_C    Foobarbazd    Foobarbaze    Foobarbazf    Foo Bar Baz G    Foo Bar Baz H    Foo Bar Baz I
    Keyword deduplicate and normalize case

One Tag
    [Tags]    One_Tag_Various Cases
    One Tag Keyword

Multiline tags
    [Tags]    Tag1    Tag2    Tag3    Tag4    Tag5    # comment1    # comment2

*** Keywords ***
Keyword no tags
    No Operation

Keyword normalize case
    [Tags]    Foo_Bar_Baz_A    Foo_Bar_Baz_B    Foo_Bar_Baz_C    Foobarbazd    Foobarbaze    Foobarbazf    Foo Bar Baz G    Foo Bar Baz H    Foo Bar Baz I
    No Operation

Keyword deduplicate
    [Tags]    Tag_A    Tag_B    Tag_C    # comment
    No Operation

Keyword deduplicate and normalize case
    [Tags]    Foo_Bar_Baz_A    Foo_Bar_Baz_B    Foo_Bar_Baz_C    Foobarbazd    Foobarbaze    Foobarbazf    Foo Bar Baz G    Foo Bar Baz H    Foo Bar Baz I
    No Operation

One Tag Keyword
    [Tags]    One_Tag_Various Cases
    No Operation
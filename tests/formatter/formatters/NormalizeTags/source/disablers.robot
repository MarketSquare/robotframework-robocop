*** Settings ***
Documentation       OrderTags acceptance tests
Force Tags          tag1    Tag2    TAG3    tag4    tag4    tag5    TAG5    # comment  # robocop: fmt: off
# robocop: fmt: off
Default Tags        tag1    Tag2    TAG3    tag4    tag4    tag5    TAG5    # comment

*** Test Cases ***
No tags
    Keyword no tags

Normalize case
    [Tags]    foo_bar_baz_a    Foo_Bar_Baz_b    FOO_BAR_BAZ_c     foobarbazd    FooBarBaze    FOOBARBAZf    foo bar baz g    Foo Bar Baz h    FOO BAR BAZ i  # robocop: fmt: off
    Keyword normalize case

Deduplicate
    [Tags]    tag_a   tag_a   tag_b    tag_c  # robocop: fmt: off
    Keyword deduplicate

Deduplicate and normalize case
    # robocop: fmt: off
    [Tags]    foo_bar_baz_a    foo_bar_baz_A    Foo_Bar_Baz_b    FOO_BAR_BAZ_c     foobarbazd    FooBarBaze    FOOBARBAZf    foo bar baz g    Foo Bar Baz h    FOO BAR BAZ i
    Keyword deduplicate and normalize case
# robocop: fmt: off
One Tag
    [Tags]    One_Tag_various CASES
    One Tag Keyword

Multiline tags
    [Tags]    tag1
    ...    Tag2
    ...    TAG3    # comment1
    ...    tag4
    ...    tag4
    ...    tag5    # comment2
    ...    TAG5

*** Keywords ***
Keyword no tags
    No Operation

Keyword normalize case
    # robocop: fmt: off
    [Tags]    foo_bar_baz_a    Foo_Bar_Baz_b    FOO_BAR_BAZ_c     foobarbazd    FooBarBaze    FOOBARBAZf    foo bar baz g    Foo Bar Baz h    FOO BAR BAZ i
    No Operation

Keyword deduplicate
    [Tags]    tag_a   tag_a   tag_b    tag_c    # comment  # robocop: fmt: off
    No Operation
# robocop: fmt: off
Keyword deduplicate and normalize case
    [Tags]    foo_bar_baz_a    foo_bar_baz_A    Foo_Bar_Baz_b    FOO_BAR_BAZ_c     foobarbazd    FooBarBaze    FOOBARBAZf    foo bar baz g    Foo Bar Baz h    FOO BAR BAZ i
    No Operation

One Tag Keyword
    [Tags]    One_Tag_various CASES
    No Operation
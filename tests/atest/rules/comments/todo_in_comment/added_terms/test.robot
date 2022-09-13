*** Settings ***
Documentation  doc  # todo so many things


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    One More

# fixme: this whole section
*** Keywords ***  # TODO do this
Keyword  # FIXME now!
    [Documentation]  this is doc
    No Operation  # todo: do something
    Pass
    No Operation
    # OMG! It's alive!
    Fail

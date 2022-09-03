*** Settings ***
Documentation  doc  # todo so many things


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    One More

# remove me: this whole section
*** Keywords ***  # TODO do this
Keyword  # FIXME now!
    [Documentation]  this is doc
    No Operation  # todo: do something
    Pass
    # FIX this UGLY bug!!
    No Operation
    # KORJAA TÄMÄ HÄSSÄKKÄ!
    Fail

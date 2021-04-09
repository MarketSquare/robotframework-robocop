*** Settings ***
Documentation  doc
Library    Collections                                                                                                                                     


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    Keyword With Looooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooong Name And  ${args}

Test with disabler
    Keyword That Is Quite Long But Under The Limit     ${arg}    ${arg}    ${arg}    ${arg}    ${arg}    ${arg}  # robocop: disable=0101
    Keyword That Is Quite Long But Under The Limit     ${arg}    ${arg}    ${arg}    ${arg}    ${arg}    ${arg}              # robocop: enable
    Keyword That Is Quite Long But Under The Limit     ${arg}    ${arg}    ${arg}    ${arg}    ${arg}    ${arg}              # noqa


*** Keywords ***
Keyword
	[Documentation]  this is looooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooong doc
    No Operation
    Pass
    Keyword With Looooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooong Name And  ${args}
    Fail

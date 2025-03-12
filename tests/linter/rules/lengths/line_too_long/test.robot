*** Settings ***
Documentation  doc
Library    Collections                                                                                                                                     
Metadata    ENV_URL    http://example.com/blob/5f96098d658fd9c1b59c5f1675033485e1b3bad05f96098d658fd9c1b59c5f1675033485e1b3bad0/args?param=101205f96098d658fd9c1b59c5f1675033485e1b3bad0


*** Variables ***
${MY_VARIABLE}    Liian pitkä rivi, jossa on ääkkösiä. Pituuden tarkistuksen pitäisi laskea merkkejä, eikä tavuja.


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    Keyword With Looooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooong Name And  ${args}

Test with disabler
    Keyword That Is Quite Long But Under The Limit     ${arg}    ${arg}    ${arg}    ${arg}    ${arg}    ${arg}  # robocop: off=0101
    Keyword That Is Quite Long But Under The Limit     ${arg}    ${arg}    ${arg}    ${arg}    ${arg}    ${arg}              # robocop: on
    Keyword That Is Quite Long But Under The Limit     ${arg}    ${arg}    ${arg}    ${arg}    ${arg}    ${arg}              # noqa


*** Keywords ***
Keyword
	[Documentation]  this is looooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooong doc
    No Operation
    Pass
    Keyword With Looooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooong Name And  ${args}
    Fail

Keyword With Unicode
    This Is ąęłżź ąęłżź ąęłżź ąęłżź ąęłżź ąęłżź ąęłżź ąęłżź ąęłżź ąęłżź ąęłżź ąęłżź ąęłżź
    日本語 日本語 日本語 日本語 日本語 日本語 日本語 日本語 日本語 日本語 日本語 日本語 日本語 日本語
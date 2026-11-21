*** Settings ***
Resource    resources/a/util.resource


*** Test Cases ***
Suite Keyword Is Not Called With Prefix
    util.Shared Keyword


*** Keywords ***
Shared Keyword
    Log    from suite

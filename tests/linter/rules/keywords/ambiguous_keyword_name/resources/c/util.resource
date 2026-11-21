*** Settings ***
Resource    ../a/util.resource
Resource    ../b/util.resource


*** Keywords ***
Shared Keyword
    Log    from c

Call Shared From Resource
    util.Shared Keyword

*** Settings ***
Resource    ../resources/a/util.resource
Resource    ../resources/b/util.resource


*** Test Cases ***
Search Order Does Not Resolve Prefixed Calls
    Set Library Search Order    util
    util.Shared Keyword

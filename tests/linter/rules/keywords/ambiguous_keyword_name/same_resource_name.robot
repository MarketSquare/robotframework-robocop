*** Settings ***
Resource    resources/a/util.resource
Resource    resources/b/util.resource


*** Test Cases ***
Ambiguous Prefixed Call
    util.Shared Keyword

Prefixed Call Matching Single Resource
    util.Only In A

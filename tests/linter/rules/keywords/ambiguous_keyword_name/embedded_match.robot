*** Settings ***
Resource    resources/a/util.resource
Resource    resources/b/util.resource
Resource    resources/embedded/util.resource


*** Test Cases ***
Ambiguous Prefixed Call Despite Embedded Match
    util.Shared Keyword

Ambiguous Call Despite Embedded Match
    Shared Keyword

Embedded Match Only
    util.Shared Value

*** Settings ***
Suite Setup  Run Keyword If
Suite Teardown  Run Keyword If

Test Setup  Run Keyword If
Test Teardown  Run Keyword If

*** Test Cases ***
Test
    [Setup]  Run Keyword Unless
    [Teardown]  Run Keyword Unless
    Run Keyword Unless   True   Hello World
    Run Keyword If   True   Hello World
    run_keyword_unless   True   Hello World
    builtin.run_KeywoRD_UNLESS   True   Hello World
    BuiltIn.Run Keyword Unless   True   Hello World

Templated test
    [Template]    Run Keyword Unless

*** Settings ***
Suite Setup    Log Many    %{TEST STATUS}    ${TEST STATUS}    @{TEST TAGS}    ${TEST TAGS}    ${TEST MESSAGE}

*** Test Cases ***
Exact Identifier Matching
    Log Many    %{SUITE STATUS}    ${TEST STATUS}    @{TEST TAGS}
    Log    escaped \${SUITE STATUS}

*** Variables ***
${TEST STATUS}    user value
@{TEST TAGS}    user value
@{TEST MESSAGE}    wrong identifier

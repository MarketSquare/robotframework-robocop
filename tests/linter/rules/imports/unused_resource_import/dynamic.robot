*** Settings ***
Resource    resources/unused.resource

*** Variables ***
${KEYWORD_NAME}    Never Called

*** Test Cases ***
Test
    Run Keyword    ${KEYWORD_NAME}
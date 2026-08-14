*** Settings ***
Resource    resources/common.resource
Resource    resources/missing.resource
Resource    ${RESOURCE_DIR}/common.resource
Resource    ${UNDEFINED_DIR}/other.resource
Library     Collections

*** Variables ***
${RESOURCE_DIR}      resources

*** Test Cases ***
Test
    Common Keyword

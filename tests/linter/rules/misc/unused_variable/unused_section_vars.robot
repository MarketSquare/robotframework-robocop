*** Settings ***
Documentation    Global variables in test/task files cannot be imported and should be used within file.
Library    TestLibrary    value with ${USED_IN_LIB_ARG}    ${USED_IN_LIB_ARG2}
Library    ${TEST_LIBRARY}
Resource    path/to/${GLOBAL_PATH}/file.resource
Variables    ${VARIABLES_FILE}
Variables    variables.py    @{GLOBAL_VARS_ARGS}

Suite Setup    ${SETUP_KW}
Suite Teardown    Suite Teardown    ${SUITE_TEARDOWN_ARG}
Test Setup   Test Setup    value with ${TEST_SETUP_ARG}
Test Teardown   Test Teardown    value with ${TEST_SETUP_ARG}

Metadata    Key    ${METADATA_VALUE}

Default Tags    @{DEFAULT_TAGS}


*** Variables ***
${GLOBAL_USED}    value
${GLOBAL_NOT_USED}    value
${GLOBAL_USED_IN_SECTION}    value
${GLOBAL_USED2}    value with ${GLOBAL_USED_IN_SECTION}
${USED_IN_ARG_DEFAULT}    value
${USED_IN_ARG_DEFAULT2}    value
${USED_IN_LIB_ARG}    value
${USED_IN_LIB_ARG2}    value
${TEST_LIBRARY}    value
${GLOBAL_PATH}    resources
${VARIABLES_FILE}    variables.yaml
@{GLOBAL_VARS_ARGS}    arg1    arg2
@{DEFAULT_TAGS}    tag1    tag2
${SETUP_KW}    Setup Keyword
${SUITE_TEARDOWN_ARG}    value
${TEST_SETUP_ARG}    value
${METADATA_VALUE}    value
@{TEMPLATE_ARGS}    arg1   arg2
${VAR_DOCUMENTATION}    Documentation value
${VAR_TAG}              Tag value


*** Test Cases ****
Test
    [Documentation]    Use one global variable and call keyword that uses second.
    Log    ${GLOBAL_USED}
    Keyword

Test with template
    [Template]    Template
    @{TEMPLATE_ARGS}

Test variable in documentation
    [Documentation]    ${VAR_DOCUMENTATION}
    No Operation

Test variable in tags
    [Documentation]    Documentation in test about variable in tags
    [Tags]    ${VAR_TAG}
    No Operation


*** Keywords ***
Keyword
    [Documentation]    Use second global variable.
    Log    ${GLOBAL_USED2}

Keyword With Arguments
    [Arguments]    ${arg}=${USED_IN_ARG_DEFAULT}    ${arg2}=value with ${USED_IN_ARG_DEFAULT2}
    No Operation

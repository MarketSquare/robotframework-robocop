*** Variables ***
${TEST_NAME}    value
@{TEST_TAGS}    value
${TEST_DOCUMENTATION}    value
${TEST_STATUS}    value
${TEST_MESSAGE}    value
${PREV_TEST_NAME}    value
${PREV_TEST_STATUS}    value
${PREV_TEST_MESSAGE}    value
${SUITE_NAME}    value
${SUITE_SOURCE}    value
${SUITE_DOCUMENTATION}    value
&{SUITE_METADATA}    value
${SUITE_STATUS}    value
${SUITE_MESSAGE}    value
${KEYWORD_STATUS}    value
${KEYWORD_MESSAGE}    value
${LOG_LEVEL}    value
${OUTPUT_FILE}    value
${LOG_FILE}    value
${REPORT_FILE}    value
${DEBUG_FILE}    value
${OUTPUT_DIR}    value
&{OPTIONS}    value


*** Test Cases ***
Test
    Use    ${TEST_NAME}    @{TEST_TAGS}    ${TEST DOCUMENTATION}    ${TEST STATUS}    ${TEST MESSAGE}
    ...    ${PREV TEST NAME}    ${PREV TEST STATUS}    ${PREV TEST MESSAGE}    ${SUITE NAME}    ${SUITE SOURCE}
    ...    ${SUITE DOCUMENTATION}    &{SUITE METADATA}    ${SUITE STATUS}    ${SUITE MESSAGE}    ${KEYWORD STATUS}
    ...    ${KEYWORD MESSAGE}    ${LOG LEVEL}    ${OUTPUT FILE}    ${LOG FILE}    ${REPORT FILE}    ${DEBUG FILE}
    ...    ${OUTPUT DIR}    &{OPTIONS}
    ${testname}    ${test_tags}    ${TEST_DOCUMENTATION}    ${TEST_STATUS}    Overwrite
    ${testMessage}    ${prevtestname}    ${PREV_TEST_STATUS}    ${PREV TEST MESSAGE}    Overwrite
    ${SUITE NAME}    ${SUITE SOURCE}    ${SUITE DOCUMENTATION}    ${SUITE METADATA}    Overwrite
    ${SUITE STATUS}    ${SUITE MESSAGE}    ${KEYWORD STATUS}    ${KEYWORD MESSAGE}
    ...    ${LOG LEVEL}    ${OUTPUT FILE}    ${LOG FILE}    ${REPORT FILE}    Overwrite
    ${DEBUG FILE}    IF    ${SUITE_SOURCE}    Keyword    ${LOG_FILE}
    ${OUTPUT DIR}    ${OPTIONS}    Overwrite


*** Keywords ***
Keyword
    [Arguments]    ${variable}    ${log_level}
    Log    ${log_level}
    ${keyword_status} =  IF   $cond    Keyword

Keyword with ${log_level} and ${suite_documentation:[a-z]}
    Log    ${log_level}

Item Assignment
    ${SUITE METADATA}[key]    Set Variable    ${1}

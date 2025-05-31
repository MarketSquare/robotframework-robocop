*** Keywords ***
Keyword Where Attribute Was Recognized As Most Common Sign
    ${DAT}[ReturnValue]    Generate Random String    length=${DAT}[InputValue]
    ${middle_text}     Get Text From Box    MIDDLE
    Press Screen Key    ONE
    Wait Until Box Is Unequal  MIDDLE  ${middle_text}
    Log    ${DAT}
    Set Test Message    Test ${SUITE_NAME}.${TEST_NAME} passed.

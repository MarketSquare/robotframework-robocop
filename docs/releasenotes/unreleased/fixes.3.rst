Variable not detected as used in [Tags] and [Documentation] (#1070)
-------------------------------------------------------------------

I0920 ``unused-variable`` was incorrectly raised even if variable was used in Test Case / Keyword ``[Tags]`` or
``[Documentation]``. Following code should not raise any issue anymore::

    *** Variables ***
    ${VAR_DOCUMENTATION}    Documentation value
    ${VAR_TAG}              Tag value


    *** Test Cases ***
    Test variable in documentation
        [Documentation]    ${VAR_DOCUMENTATION}
        No Operation

    Test variable in tags
        [Documentation]    Documentation in test about variable in tags
        [Tags]    ${VAR_TAG}
        No Operation

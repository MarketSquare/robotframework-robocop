Community rule: not-allowed-keyword (#1067)
-------------------------------------------

New community (optional) rule W10002 ``not-allowed-keyword``. You can use this rule to find keywords that should not
be used in your project.

For example with following configuration::

    > > robocop -i not-allowed-keyword -c not-allowed-keyword:keywords:click_using_javascript,click_with_sleep

It will find and raise issues in the following code::

    *** Test Cases ***
    Test with obsolete keyword
        [Setup]    Click With Sleep    1 min  # Robocop will report not allowed keyword
        Test Step


    *** Keywords ***
    Keyword With Obsolete Implementation
        [Arguments]    ${locator}
        Click Using Javascript    ${locator}  # Robocop will report not allowed keyword


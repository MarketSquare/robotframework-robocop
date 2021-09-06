*** Settings ***
Suite Setup    Given Keyword
Suite Teardown    Given

Test Setup    Given
Test Teardown    Then  Keyword With  ${args}

*** Test Cases ***
Valid Login
    Given login page is open
    When valid username and password are inserted
    and credentials are submitted
    But Still Authorized
    Then welcome page should be open

Invalid Empty
    [Setup]  Given
    Given
    When
    But
    IF  ${condtion}
        and
    END
    FOR  ${var}  IN RANGE  10
        Then
    END
    [Teardown]  Then

Invalid Separator
    Given  login page is open
    When  valid username and password are inserted
    and  credentials are submitted
    But  still Authorized
    Then  welcome page should be open

*** Keywords ***
Valid Login Keyword
    Given login page is open
    When valid username and password are inserted
    and credentials are submitted
    but still authorized
    Then welcome page should be open

Invalid Empty Keyword
    Given
    When
    and
    BuT
    Then

Invalid Separator Keyword
    Given  ${variable}
    When  %valid username and password are inserted
    and  credentials are submitted
    But  still authorized
    Then  welcome page should be open

Language: fi

*** Settings ***
Resurssi    shadow.resource


*** Test Cases ***
Localized resource can shadow wrapper
    [Tags]    robot:continue-on-failure
    Run Keyword And Continue On Failure    Should Not Be Unwrapped

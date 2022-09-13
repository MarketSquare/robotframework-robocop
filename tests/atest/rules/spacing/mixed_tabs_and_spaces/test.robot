*** Settings ***
Documentation	Suite documentation.
Force Tags    logging


*** Variables ***
@{RANDOM_LIST}    first_element	second_element


*** Test Cases ***
Test Which Includes Tabs And Spaces
    [Documentation]    Test documentation.
    Log Two Elements To Console    @{RANDOM_LIST}


*** Keywords ***
Log Two Elements To Console
    [Documentation]	Keyword documentation.
    [Arguments]    ${first_element}    ${second_element}
    Log To Console    ${first_element}	${second_element}
    Log To Console	    ${second_element}    	${first_element}


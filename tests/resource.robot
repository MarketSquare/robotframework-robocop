*** Variables ***
${var}  5

*** Keywords ***
My External Keywords
    [Arguments]  ${arg1}=0  ${aRg2}=0
    [Tags]  tag  TAG  tag with space
    [Idontexist]  dd
	[Documentation]  This is example documentation
	Log Many  ${arg1}
	...  ${arg2}
	${var}    I return smth
	Log  ${var}
	Set Global Variable  ${var}
	[Return]  ${var}
	Log  ${arg1}
	
*** Not Existing ***
${var5}  10

*** Empty ***

*** Keywords ***
I return smth
   [Return]  5
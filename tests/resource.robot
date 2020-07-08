*** Variables ***
${var}  5

*** Keywords ***
My External Keywords
    [Arguments]  ${arg1}=0  ${arg2}=0
	[Documentation]  This is example documentation
	Log Many  ${arg1}  ${arg2}
	[Return]  ${var}
	
*** Not Existing ***
${var5}  10

*** Empty ***
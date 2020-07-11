# first line comment TODO:
*** Variables ***
${var}  5

*** Keywords ***  # section comment
My External Keywords
    [Arguments]  ${arg1}=0  ${aRg2}=0
    [Tags]  tag  TAG  tag with space
    [Idontexist]  dd  # robocop: disable=parsing-error
	[Documentation]  This is example documentation
	Log Many  ${arg1}
	...  ${arg2}
	${var}    I return smth
	Log  ${var}
	Set Global Variable  ${var}
	[Return]  ${var}
	Log  ${arg1}  # keyword comment fixme:
	
*** Not Existing ***
${var5}  10
# robocop: disable
*** Empty ***
# robocop: enable
*** Keywords ***
I return smth
   [Return]  5
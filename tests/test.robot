*** Settings ***
Resource   resource.robot
Variables  vars.robot
Library    robot_lib.py
Force Tags    forcedtag
Default Tags  defaulttag  default with space

*** Test Cases ***
Test
    Log  1
	My Internal Keyword
	#  in line comment
	My External Keyword  ${arg1}  ${arg2}=3
    # in line comment


Test
    Log  2
	
Test With Invalid Char.
    Log  1

*** Keywords ***
My Internal Keyword
    [Documentation]  This is doc
    Log  My Interal Keyword  # extra comment ${arg}
	
Missing Keyword Documentation  # robocop: disable=rule1,rule2
    Log  1
	
Missing Doc But Disabled Rule  # roblint: disable=missing-doc-keyword
    Log  2
	
Keyword With Invalid Char?
    Log  1

Keyword With Reserved Tags
    [Tags]  tagORtag  tagorand  andsmth  with space or reserved
*** Settings ***
Resource   ${CURDIR}${/}resource.robot
Resource   ${EXECDIR}${/}tests${/}resource.robot
Variables  vars.robot
Library    robot_lib.py
Force Tags    forcedtag
Force Tags    lol
Library   robot_lib.py  AS  smth
Default Tags  defaulttag  default with space

*** Test Cases ***
Test
    Log  1
    My Internal Keyword
    #  in line comment
    My External Keyword  ${arg1}  ${arg2}=3
   Log  1
    # in line comment
    #comment without space


Test
    Log  2

Test With Invalid Char.
    Log  1

This Is Quite Long Line Which Is Veeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeery Long
    Log                                                                                                                         Late argument

 # test comment
  # test comment


*** Keywords ***
My Internal Keyword
    [Documentation]  This is doc
    Log  My Interal Keyword  # extra comment ${arg}

Missing Keyword Documentation  # robocop: disable=rule1,rule2
    Log  1

Missing Doc But Disabled Rule  # roblint: disable=missing-doc-keyword
    Log  2

Keyword With Invalid Char?
    Log  19
    [Teardown]  pass execution

Keyword With Reserved Tags
    [Tags]  tagORtag  tagorand  andsmth  with space or reserved  robot:no-dry-run  robot:my_tag

 # test comment
  # test comment

*** Settings ***
Library    Collections
Library    XML
Library    String
Resource   ..${/}Libs${/}MyResource.robot
Variables    variables.py
Test Template    Keyword
Library    BuiltIn


*** Keywords ***
Keyword
    No Operation

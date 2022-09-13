*** Settings ***
Library    Collections
Library    String
Library    XML
Library    DateTime
Library    OperatingSystem
Resource   ..${/}Libs${/}MyResource.robot
Variables    variables.py
Test Template    Keyword
Library    BuiltIn


*** Keywords ***
Keyword
    No Operation

*** Settings ***
Library    Collections
Library    String
Library    XML
Library    RequestsLibrary
Library    DateTime
Library    OperatingSystem
Resource   ..${/}Libs${/}MyResource.robot
Library    OwnLib.py
Variables    variables.py
Test Template    Keyword
Library    BuiltIn


*** Keywords ***
Keyword
    No Operation

*** Settings ***
Library    Collections
Library    RequestsLibrary
Library    OperatingSystem  # builtin after custom
Resource    resource.robot
Library    OwnLib.py
Library    XML
...    use_lxml=True


*** Keywords ***
Keyword
    No Operation

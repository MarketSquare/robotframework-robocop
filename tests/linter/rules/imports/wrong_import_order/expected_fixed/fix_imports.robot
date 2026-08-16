*** Settings ***
Library    Collections
Library    OperatingSystem  # builtin after custom
Library    XML
...    use_lxml=True
Library    RequestsLibrary
Resource    resource.robot
Library    OwnLib.py


*** Keywords ***
Keyword
    No Operation

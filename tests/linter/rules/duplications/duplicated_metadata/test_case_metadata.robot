*** Settings ***
Metadata    Owner    QA


*** Test Cases ***
Test With Duplicated Metadata
    [Metadata]    Owner    QA
    [Metadata]    Ticket    RF-4409
    [Metadata]    Owner    QA
    Keyword

Test With Metadata Repeated From Other Scopes
    [Metadata]    Owner    QA
    [Metadata]    Ticket    RF-4409
    Keyword


*** Keywords ***
Keyword
    No Operation

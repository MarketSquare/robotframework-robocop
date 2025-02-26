*** Settings ***
Documentation       docs

Library             String
Resource            some_file.py
Variables           some_file.py
Keyword Tags        tag

Name                Some name
Metadata            something
Suite Setup         Keyword
Suite Teardown      Keyword
Test Tags           one    two
Test Setup          Keyword
Test Teardown       Keyword
Test Template       Template
Test Timeout        1000
Force Tags          tag
Default Tags        tag

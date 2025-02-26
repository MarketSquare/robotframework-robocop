*** Settings ***
Test Tags    Simple    With ${VAR}
Default Tags    Simple    With ${VAR lower}


*** Test Cases ***
No tags
    Keyword no tags

Tags
    [Tags]    Simple    With ${VAR}    ${tag}    ${tag} After
    One Tag Keyword

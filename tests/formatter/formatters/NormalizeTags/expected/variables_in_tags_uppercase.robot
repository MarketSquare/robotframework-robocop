*** Settings ***
Test Tags    SIMPLE    WITH ${VAR}
Default Tags    SIMPLE    WITH ${VAR lower}


*** Test Cases ***
No tags
    Keyword no tags

Tags
    [Tags]    SIMPLE    WITH ${VAR}    ${tag}    ${tag} AFTER
    One Tag Keyword

*** Settings ***
Test Tags          simple    WITH ${VAR}
Default Tags        SIMPLE    with ${VAR lower}


*** Test Cases ***
No tags
    Keyword no tags

Tags
    [Tags]    SIMPLE    with ${VAR}    ${tag}
    ...    ${tag} after
    One Tag Keyword

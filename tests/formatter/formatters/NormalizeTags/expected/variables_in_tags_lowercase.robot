*** Settings ***
Test Tags    simple    with ${VAR}
Default Tags    simple    with ${VAR lower}


*** Test Cases ***
No tags
    Keyword no tags

Tags
    [Tags]    simple    with ${VAR}    ${tag}    ${tag} after
    One Tag Keyword

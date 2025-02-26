*** Keywords ***
[Return]
    ${local}    Set Variable    value
    [Return]    ${local}    ${GLOBAL}

RETURN
    ${local}    Set Variable    value
    RETURN    ${local}    ${GLOBAL}

Set Variable
    ${local}    Set Variable    value
    ${local2}    Set Variable    value
    ${local3}    Set Variable    value
    ${local4}    Set Variable    value
    @{local_list}    Keyword
    &{local_dict}    Keyword
    Set Test Variable
    Set Test Variable    ${LOCAL}
    Set Task Variable    $LOCAL2
    Set Suite Variable    \${LOCAL3}
    Set Global Variable    @{LOCAL_LIST}    value    ${GLOBAL_VALUE}
    Set Global Variable    &LOCAL_DICT
    Set Global Variable    ${LOCAL_${local4}}
    Log Many    ${LOCAL}    ${LOCAL2}    ${LOCAL3}    ${local4}    @{LOCAL_LIST}    ${LOCAL_DICT}
    Set Local Variable    $local_list
    Set Local Variable    ${local2}
    Log Many    ${LOCAL}    ${local2}    ${LOCAL3}    ${local4}    @{local_list}    ${LOCAL_DICT}

*** Keywords ***
[Return]
    ${local}    Set Variable    value
    [Return]    ${local}    ${global}

RETURN
    ${local}    Set Variable    value
    RETURN    ${local}    ${global}

Set Variable
    ${local}    Set Variable    value
    ${local2}    Set Variable    value
    ${local3}    Set Variable    value
    ${local4}    Set Variable    value
    @{local_list}    Keyword
    &{local_dict}    Keyword
    Set Test Variable
    Set Test Variable    ${local}
    Set Task Variable    $local2
    Set Suite Variable    \${local3}
    Set Global Variable    @{local_list}    value    ${global_value}
    Set Global Variable    &local_dict
    Set Global Variable    ${local_${local4}}
    Log Many    ${local}    ${local2}    ${local3}    ${local4}    @{local_list}    ${local_dict}
    Set Local Variable    $local_list
    Set Local Variable    ${local2}
    Log Many    ${local}    ${local2}    ${local3}    ${local4}    @{local_list}    ${local_dict}

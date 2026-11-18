*** Keywords ***
Wait For Order State
    [Arguments]    ${order}    ${state}
    WHILE    $order.state != $state    limit=30    on_limit=fail
        ${order}=    Refresh Order    ${order}
        IF    $order.state == 'cancelled' or $order.state == 'failed'
            IF    $state == 'cancelled'
                RETURN    ${order}
            END
            Fail    Order ended in ${order.state}
        ELSE IF    $order.state == 'on_hold'
            Run Keyword If    $auto_release    Release Order    ${order}    ELSE    Notify Support    ${order}
        END
        Sleep    1s
    END

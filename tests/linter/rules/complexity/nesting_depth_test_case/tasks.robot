*** Tasks ***
Process Inbox
    FOR    ${mail}    IN    @{mails}
        TRY
            IF    $mail.spam
                WHILE    $mail.retry
                    Handle Mail    ${mail}
                END
            END
        EXCEPT    Timeout*    type=glob
            Log    timeout
        END
    END

Shallow Task
    FOR    ${mail}    IN    @{mails}
        Log    ${mail}
    END

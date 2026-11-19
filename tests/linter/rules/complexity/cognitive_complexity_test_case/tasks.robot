*** Tasks ***
Process Inbox
    FOR    ${mail}    IN    @{mails}
        IF    $mail.spam
            CONTINUE
        END
        TRY
            Handle Mail    ${mail}
        EXCEPT    Timeout*    type=glob
            IF    $retry and $online
                Retry Mail    ${mail}
            ELSE
                Skip Mail    ${mail}
            END
        EXCEPT
            Log    failed
        ELSE
            IF    $mail.flagged    Flag Mail    ${mail}
        END
    END

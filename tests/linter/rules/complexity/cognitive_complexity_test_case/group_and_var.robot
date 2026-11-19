*** Test Cases ***
Grouped Steps
    GROUP    Prepare
        VAR    ${retries}    3
        IF    $env == 'prod'
            GROUP    Prod checks
                FOR    ${check}    IN    @{checks}
                    IF    $check.critical and not $dry_run
                        Run Check    ${check}
                    ELSE IF    $check.optional
                        CONTINUE
                    ELSE
                        IF    $verbose    Log    ${check}
                    END
                END
            END
        END
    END
    GROUP    Execute
        WHILE    $retries > 0    limit=5
            VAR    ${retries}    ${retries - 1}
            IF    $done    BREAK
        END
    END

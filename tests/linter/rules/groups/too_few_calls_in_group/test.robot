*** Test Cases ***
Single keyword group
    GROUP    Login
        Log    message
    END

Two keywords group
    GROUP    Steps
        Log    a
        Log    b
    END

Unnamed single keyword group
    GROUP
        Log    only
    END

Empty group is reported by parsing-error instead
    GROUP    Empty
    END

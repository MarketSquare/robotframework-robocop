*** Test Cases ***
Named group
    GROUP    Login
        Log    message
    END

Unnamed group
    GROUP
        Log    message
    END

Nested groups
    GROUP    Outer
        GROUP    Inner
            Log    message
        END
    END

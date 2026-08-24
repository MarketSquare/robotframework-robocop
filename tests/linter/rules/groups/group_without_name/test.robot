*** Test Cases ***
Named group
    GROUP    Has name
        Log    a
    END

Unnamed group
    GROUP
        Log    a
    END

Unnamed group with several keywords
    GROUP
        Log    b
        Log    c
    END

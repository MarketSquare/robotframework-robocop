*** Test Cases ***
Empty group
    GROUP    Empty group
    END

Group without end
    GROUP    No end
        Log    message

Group with too many values
    GROUP    Too    many    values
        Log    message
    END

Valid group
    GROUP    Valid
        Log    message
    END

Valid group without name
    GROUP
        Log    message
    END

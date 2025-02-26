*** Test Cases ***
Keyword
    ${assign}    Looooooooonger Keyword Name    ${argument}
    Short    Short    Short
    Single
    Multi    ${arg}
    ...    ${arg}

Second Keyword
    Looooooooonger Keyword Name

With Comments
    Single  # comment 1
    With Arg  # comment 2  comment 3
    Multi    ${arg}  # comment 4
    ...    ${arg}    # comment 5
    Three Args    argument    argument

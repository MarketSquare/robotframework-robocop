# standalone comment

*** Settings ***
Library    Collections    # comment

# standalone

*** Keywords ***
# standalone

Keyword    # with comment
    # with comment    and    spaces
    Keyword Call    # with comment
    FOR    ${var}    IN RANGE    10    # with comment
        # with comment
        Log    ${var}
    END    # with comment

# standalone  with  some  spacing
#                                      #

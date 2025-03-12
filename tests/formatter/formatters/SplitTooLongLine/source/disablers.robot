# Use 4 spaces separator and line_length=80

*** Tasks ***

Different keyword calls
    This is a keyword     fits with its               # robocop: fmt: off comment comment comment

    This is a keyword     these args do not fit       even if you set spacing properly  # robocop: fmt: off

    # robocop: fmt: off
    This is a keyword     this    last    argument    is    not    really    a # comment

    This is a keyword     these    arguments    won't    fit    with     that   # comment

    This is a keyword     these    arguments    won't    fit    with    or    without    that   # comment

    This is a keyword     these     args    have    an    interesting
    ...  # Edge case here →→→→→→→→→→→→→→→→                                    HERE
    ...  More arguments here

    This is a keyword     and     these      are       its     args
    ...    here   are   some    more    args      to      split
    ...    with                irregular                       spacing

    ${assignment}=    This keyword sets the variable   using   these     args

    ${assignment}=    This keyword sets the variable   using   these     args
    ...    here   are   some    more    args      to      split
    ...    with                irregular                       spacing


    This is a keyword     and     these      are       its     args  # Comment

    This is a keyword     and     these      are       its     arg   # Comment
    ...    here   are   some    more    args
    ...    with                irregular                       spacing

    This is a keyword     and     these      are       its     arg   # Comment 1
    ...    here   are   some    more    args                         # Comment 2
    ...    with                irregular                     spacing # Not really a comment


    ${assignment}=    This keyword sets the variable   using   these  args  # Comment

    ${assignment}=    This keyword sets the variable   using   these     args
    ...    here   are   some    more    args      to      split            # Comment
    ...    with                irregular                       spacing

For loop
    FOR   ${i}   IN    1  2  3  4  5  6  7  8  9  10  11  12  13  14  15  16  17  18  20
        This is a keyword     these args do not fit       even if you set spacing properly  # robocop: fmt: off

        This is a keyword     these    arguments    won't    fit    with     that   # robocop: fmt: off = SplitTooLongLine

        This is a keyword     these     args    have    an    interesting
        ...  # Edge case here →→→→→→→→→→→→→→→→                                    HERE  # robocop: fmt: off
        ...  More arguments here
    END


If - else if - else clause
    IF    ${some variable with a very long name} == ${some other variable with a long name}
        ${assignment}=    This keyword sets the variable   using   these     args
        ...    here   are   some    more    args      to      split            # Comment  # robocop: fmt: off
        ...    with                irregular                       spacing
    ELSE IF    ${random} > ${NUMBER_TO_PASS_ON}
        # robocop: fmt: off
        ${assignment}=    This keyword sets the variable   using   these     args
        ...    here   are   some    more    args      to      split            # Comment
        ...    with                irregular                       spacing
    ELSE
        ${assignment}=    This keyword sets the variable   using   these     args  # robocop: fmt: off
        ...    here   are   some    more    args      to      split            # Comment
        ...    with                irregular                       spacing
    END

Too long inline IF  # shall be handled by InlineIf transformer
    ${var}    ${var2}    IF    $condition != $condition2    Longer Keyword Name    ${argument}    values    ELSE IF    $condition2    Short Keyword    ${arg}  # comment

Multiple Assignments
    ${first_assignment}    ${second_assignment}    My Keyword
    ${first_assignment}    ${second_assignment}    Some Lengthy Keyword So That This Line Is Too Long          ${arg1}      ${arg2}  # robocop: fmt: off
    ${multiline_first}
    ...    ${multiline_second}=    Some Lengthy Keyword So That This Line Is Too Long  # robocop: fmt: off
    # robocop: fmt: off
    ${first_assignment}    ${second_assignment}    ${third_assignment}    Some Lengthy Keyword So That This Line Is Too Long And Bit Over    ${arg1}    ${arg2}

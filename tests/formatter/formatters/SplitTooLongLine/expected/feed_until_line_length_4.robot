# Use 4 spaces separator and line_length=80

*** Tasks ***

Different keyword calls
    This is a keyword     fits even with its    # comment

    # comment, but has bad spacing
    This is a keyword    fits with its

    This is a keyword    these fit    but    only if you space them correctly

    This is a keyword    these args do not fit
    ...    even if you set spacing properly

    This is a keyword    this    last    argument    is    not    really
    ...    a # comment

    # comment
    This is a keyword    these    arguments    won't    fit    with    that

    # comment
    This is a keyword    these    arguments    won't    fit    with    or
    ...    without    that

    # Edge case here →→→→→→→→→→→→→→→→                                    HERE
    This is a keyword    these    args    have    an    interesting    ${EMPTY}
    ...    More arguments here

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

    # Comment 1
    # Comment 2
    This is a keyword    and    these    are    its    arg    here    are
    ...    some    more    args    with    irregular
    ...    spacing # Not really a comment


    # Comment
    ${assignment}=    This keyword sets the variable    using    these    args

    # Comment
    ${assignment}=    This keyword sets the variable    using    these    args
    ...    here    are    some    more    args    to    split    with
    ...    irregular    spacing


Newlines
    Keyword

    # Newlines with trailing space are not changed
        
        

    Keyword


For loop
    FOR   ${i}   IN    1  2  3  4  5  6  7  8  9  10  11  12  13  14  15  16  17  18  20
        This is a keyword     fits even with its    # comment

        # comment, but has bad spacing
        This is a keyword    fits with its

        This is a keyword    these fit    but only if you space them correctly

        This is a keyword    these args do not fit
        ...    even if you set spacing properly

        This is a keyword    this    last    argument    is    not    really
        ...    a # comment

        # comment
        This is a keyword    these    arguments    won't    fit    with    that

        # comment
        This is a keyword    these    arguments    won't    fit    with    or
        ...    without    that

        # Edge case here →→→→→→→→→→→→→→→→                                    HERE
        This is a keyword    these    args    have    an    interesting
        ...    ${EMPTY}    More arguments here

        This is a keyword     and     these      are       its     args
        ...    here   are   some    more    args      to      split
        ...    with                irregular                       spacing

        ${assignment}=    This keyword sets the variable    using    these
        ...    args

        ${assignment}=    This keyword sets the variable    using    these
        ...    args    here    are    some    more    args    to    split
        ...    with    irregular    spacing


        # Comment
        This is a keyword    and    these    are    its    args

        # Comment
        This is a keyword    and    these    are    its    arg    here    are
        ...    some    more    args    with    irregular    spacing

        # Comment 1
        # Comment 2
        This is a keyword    and    these    are    its    arg    here    are
        ...    some    more    args    with    irregular
        ...    spacing # Not really a comment


        # Comment
        ${assignment}=    This keyword sets the variable    using    these
        ...    args

        # Comment
        ${assignment}=    This keyword sets the variable    using    these
        ...    args    here    are    some    more    args    to    split
        ...    with    irregular    spacing
    END


If - else if - else clause
    IF    ${some variable with a very long name} == ${some other variable with a long name}
        # Comment
        ${assignment}=    This keyword sets the variable    using    these
        ...    args    here    are    some    more    args    to    split
        ...    with    irregular    spacing
    ELSE IF    ${random} > ${NUMBER_TO_PASS_ON}
        # Comment
        ${assignment}=    This keyword sets the variable    using    these
        ...    args    here    are    some    more    args    to    split
        ...    with    irregular    spacing
    ELSE
        # Comment
        ${assignment}=    This keyword sets the variable    using    these
        ...    args    here    are    some    more    args    to    split
        ...    with    irregular    spacing
    END

Too long inline IF  # shall be handled by InlineIf transformer
    # comment
    ${var}    ${var2}    IF    $condition != $condition2    Longer Keyword Name
    ...    ${argument}    values    ELSE IF    $condition2    Short Keyword
    ...    ${arg}

Keyword name over the limit
    Enter "${VNFname}" in the field with XPath "//label[contains(text(), 'Product Name')]/../mat-form-field/div/div/div/textarea"

    ${assign}
    ...    Enter "${VNFname}" in the field with XPath "//label[contains(text(), 'Product Name')]/../mat-form-field/div/div/div/textarea"

    ${assign}
    ...    ${assign}
    ...    Enter "${VNFname}" in the field with XPath "//label[contains(text(), 'Product Name')]/../mat-form-field/div/div/div/textarea"

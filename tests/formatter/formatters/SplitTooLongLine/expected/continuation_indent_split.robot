*** Keywords ***
Keyword
    This is a keyword  # Edge case here →→→→→→→→→→→→→→→→                                    HERE
    ...    these
    ...    args
    ...    have
    ...    an
    ...    interesting
    ...    ${EMPTY}
    ...    More arguments here

    This is a keyword  # Comment 1 Comment 2
    ...    and
    ...    these
    ...    are
    ...    its
    ...    arg
    ...    here
    ...    are
    ...    some
    ...    more
    ...    args
    ...    with
    ...    irregular
    ...    spacing # Not really a comment

    ${assignment}=  This keyword sets the variable  # Comment
    ...    using
    ...    these
    ...    args
    ...    here
    ...    are
    ...    some
    ...    more
    ...    args
    ...    to
    ...    split
    ...    with
    ...    irregular
    ...    spacing

    ${assign}
    ...    ${assign}
    ...    Enter "${VNFname}" in the field with XPath "//label[contains(text(), 'Product Name')]/../mat-form-field/div/div/div/textarea"

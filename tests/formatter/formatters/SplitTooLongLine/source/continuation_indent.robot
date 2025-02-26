*** Keywords ***
Keyword
    This is a keyword     these     args    have    an    interesting
    ...  # Edge case here →→→→→→→→→→→→→→→→                                    HERE
    ...  More arguments here

    This is a keyword     and     these      are       its     arg   # Comment 1
    ...    here   are   some    more    args                         # Comment 2
    ...    with                irregular                     spacing # Not really a comment

    ${assignment}=    This keyword sets the variable   using   these     args
    ...    here   are   some    more    args      to      split            # Comment
    ...    with                irregular                       spacing

    ${assign}    ${assign}     Enter "${VNFname}" in the field with XPath "//label[contains(text(), 'Product Name')]/../mat-form-field/div/div/div/textarea"

*** Keywords ***
TRY EXCEPT example
    ${initial}    Keyword
    TRY
        ${initial}    Keyword
        ${initial_from_try}    Keyword
        ${initial_from_try2}    Keyword
    EXCEPT     Error message*  AS  ${error}
        ${initial_from_except}    Keyword
        ${initial_from_except2}    Keyword
    FINALLY
        ${initial_from_finally}    Keyword
        ${initial_from_finally2}    Keyword
    ELSE
        ${initial_from_else}    Keyword
        ${initial_from_else2}    Keyword
    END
    ${initial_from_try}    Keyword
    ${initial_from_except}    Keyword
    ${initial_from_finally}    Keyword
    ${initial_from_else}    Keyword
    ${error}    Keyword

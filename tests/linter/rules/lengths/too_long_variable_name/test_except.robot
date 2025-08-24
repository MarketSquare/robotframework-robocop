*** Settings ***
Documentation       doc


*** Test Cases ***
Test
    TRY
        No Operation
    EXCEPT    *warn*    AS    ${short_name}
        No Operation
    EXCEPT    *err*    AS    ${still_acceptable_name_for_captured_error}
        No Operation
    EXCEPT    *fatal*    AS    ${too_loong_name_for_captured_error_message}
        No Operation
    EXCEPT    *****    AS    ${another_too_long_name_for_captured_error_message}
        No Operation
    EXCEPT
        No Operation
    ELSE
        No Operation
    FINALLY
        No Operation
    END


*** Keywords ***
Some Keyword
    TRY
        No Operation
    EXCEPT    AS    ${too_loong_name_for_captured_error_message}
        No Operation
    END

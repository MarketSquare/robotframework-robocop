*** Test Cases ***
Single named group
    GROUP    Named
        Keyword Call  ${arg}
    END

Empty group
    GROUP
    END

Non-named group
    GROUP
        Keyword Call  ${arg}
    END

Nested group
    GROUP    1st level
        GROUP  2nd level
          Keyword Call  ${arg}
        END
    END

Multiline group header
    GROUP
    ...    Named
    Keyword Call
    END

Inside other control structure
    WHILE    ${True}
        GROUP  Named
            Keyword Call
        END
    END
    IF    ${True}
        GROUP  Named
            Keyword Call
        END
    END

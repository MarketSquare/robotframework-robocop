*** Test Cases ***
Test with groups
    GROUP
  Log     Not enough indent
    END
    GROUP
        Log    Enough indent
    END
    GROUP    Nested
  GROUP
      Single
  END
    END

not-capitalized-test-case-title should ignore non letters (#948)
----------------------------------------------------------------

W0308 ``not-capitalized-test-case-title`` was also reporting if the test case started with character other than letter:

```
15 - Test case with test identifier
    Prepare
    Run
    Assert
```

It should now properly check if first letter found in the test case name (ignoring other characters) is capitalized.

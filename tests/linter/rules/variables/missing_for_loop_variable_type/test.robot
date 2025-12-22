*** Test Cases ***
Test With FOR Loop
    # Should report - no type
    FOR    ${index}    IN RANGE    10
        Log    ${index}
    END
    # Should NOT report - has type
    FOR    ${value: int}    IN RANGE    10
        Log    ${value}
    END
    # Multiple variables - mixed
    FOR    ${idx}    ${date: date}    IN ENUMERATE    2023-06-15    2025-05-30
        Log    ${idx} ${date}
    END
    # Should NOT report - ignore variable
    FOR    ${_}    IN RANGE    10
        Log    Iteration
    END

Test With Nested FOR Loops
    # Outer loop - should report
    FOR    ${i}    IN RANGE    3
        # Inner loop - should report
        FOR    ${j}    IN RANGE    2
            Log    ${i} ${j}
        END
        # Inner loop with type - should NOT report
        FOR    ${k: int}    IN RANGE    2
            Log    ${i} ${k}
        END
    END
    # Outer loop with type - should NOT report
    FOR    ${x: int}    IN RANGE    3
        # Inner loop - should report
        FOR    ${y}    IN RANGE    2
            Log    ${x} ${y}
        END
    END

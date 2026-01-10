# Auto-fixing

Robocop can automatically fix certain linting issues detected in your Robot Framework files.
This feature helps maintain code quality by applying corrections directly to your code.

To enable auto-fixing, use the `--fix` flag:

```bash
robocop check --fix
```

This will automatically apply **safe** fixes to your files. Safe fixes are corrections that are guaranteed to
preserve the intended behaviour of your code.

Get the list of rules with fixes available with ``list rules``:

```bash
robocop check list rules --with-fix
```

## Fix Applicability Levels

Robocop categorizes fixes into three levels based on their risk:

### Safe Fixes

Safe fixes can be automatically applied without any risk of changing the intended behaviour of your code.
These fixes include:

- Correcting spacing and indentation
- Fixing deprecated syntax with direct replacements
- Normalizing formatting issues

Safe fixes are always applied when using `--fix`.

### Unsafe Fixes

Unsafe fixes are transformations that *might* change the behavior of your code or require careful review.
These fixes are not applied by default but can be enabled with the `--unsafe-fixes` flag:

```bash
robocop check --fix --unsafe-fixes
```

!!! warning "Review unsafe fixes"
    Always review the changes made by unsafe fixes before committing them. While these fixes follow best practices,
    they may not be appropriate for all contexts.

### Manual Fixes

Manual fixes are suggestions that require human intervention and cannot be automatically applied. These are displayed
in the output but never applied automatically, even with `--unsafe-fixes`.


### Preview what would be fixed without modifying files FIXME

Use the `--diff` mode to see what would change:

```bash
robocop check --diff
```

## Fix Statistics

After applying fixes, Robocop displays a summary showing:

* Total number of fixes applied
* Breakdown by file
* Count per rule type

Example output:

```text
Fixed 15 errors:
- tests/test_example.robot:
    3 x COM02 (missing-space-after-comment)
    2 x MISC06 (can-be-resource-file)

- tests/test_other.robot:
    10 x LEN08 (line-too-long)
```

## Iterative Fixing

Robocop may run multiple passes when fixing issues, as some fixes can reveal new issues. The tool automatically re-runs
checks up to 20 times or until no more fixes can be applied, whichever comes first.

## Best Practices

1. **Start with safe fixes**: Run `--fix` without `--unsafe-fixes` first to apply low-risk corrections
2. **Use version control**: Always commit your code before running auto-fixes so you can review changes with `git diff`
3. **Test after fixing**: Run your tests after applying fixes to ensure functionality is preserved
4. **Review unsafe fixes**: When using `--unsafe-fixes`, carefully review all changes
5. **Combine with formatting**: Consider running the formatter after auto-fixing for consistent code style:

```bash
robocop check --fix tests/
robocop format tests/
```

## Limitations

* Manual fixes are never applied automatically
* Some complex refactoring scenarios require manual intervention
* Auto-fixing may not be available for all rules

To check which rules support auto-fixing, use:

```bash
robocop list rules
```

Rules that support fixes will indicate the fix applicability level in their documentation.

# Release notes

## 7.0.0

### Features

- **Breaking change** Add option ``--extend-select`` for linter and formatter ([issue #1546](https://github.com/MarketSquare/robotframework-robocop/issues/1546))

    ``--extend-select`` allows to enable rules and formatters on top of the ``select`` configuration. It can be used to
    retain all default rules or formatters and only add additional ones:
    
    ```
    robocop check --extend-select no-embedded-keyword-arguments
    robocop format --extend-select AlignKeywordsSection --extend-select CustomFormatter
    ```

    Since previous ``--custom-formatters`` formatter option already behaved like a ``--extend-select`` option (which was
    not documented), it is now **deprecated and renamed** to ``--extend-select`` instead.
    
    It is also recommended to use ``--extend-select`` over ``--configue name.enabled=True``.

- **Breaking change** Split ``wrong-case-in-keyword-name`` rule into two separate rules ([issue #1471](https://github.com/MarketSquare/robotframework-robocop/issues/1471)):

    ``wrong-case-in-keyword-name`` which checks case convention in keyword definition name
    ``wrong-case-in-keyword-call`` which checks case convention in keyword call name
    
    It allows configuring different conventions for keyword definition and keyword call names. If you have existing
    configuration for ``wrong-case-in-keyword-name`` (you are ignoring it or configuring) you need to apply the same
    config to ``wrong-case-in-keyword-call`` to retain old behaviour.

- ``SplitTooLongLine`` can now split more settings types: Library imports, Test Tags and Keyword Tags ([issue #1454](https://github.com/MarketSquare/robotframework-robocop/issues/1454))

    Example code before and after the change:
    
    ```robotframework
    Library    CustomLibraryWithLongerNameAndSeveralArguments    first_argument    second_argument=${longer_variable_name}    WITH NAME    name
    ```
    
    ```robotframework
    Library             CustomLibraryWithLongerNameAndSeveralArguments
    ...                     first_argument
    ...                     second_argument=${longer_variable_name}
    ...                 WITH NAME    name
    ```

- Restore project checkers ([issue #1108](https://github.com/MarketSquare/robotframework-robocop/issues/1108))

    Project checkers were temporarily removed in the Robocop 6.0. There are now brought back in a new form, as a separate
    command:
    
    ```
    robocop check-project
    ```
    
    This command behaves similarly to the ``check`` command, but it only runs project rules.
    
    The project checks itself were also refactored to be more flexible. See [project checker](https://robocop.dev/stable/linter/linter/#project-checks)
    and [custom rules project checker](https://robocop.dev/stable/linter/custom_rules/#project-checks) for reference.

- Extend robocop disablers to the whole node ([issue #1515](https://github.com/MarketSquare/robotframework-robocop/issues/1515)

    Robocop will now ignore issues in the whole node (keyword, test case, for loop, keyword call, etc.) when the disabler
    is set in the header / keyword call body. For example:
    
    ```robotframework
    *** Keywords ***
    My Keyword  
        FOR    ${var}    IN    1  2  3  # robocop: off=unused-variable
             Log    1
        END
        Keyword    # robocop: off=bad-indent
        ...    ${var}
        ...    ${var2}
    ```
    
    Previously, Robocop would ignore ``unused-variable`` only when reported on the ``FOR`` header and ``bad-indent`` only
    when reported on the same line as disabler comment. After this change, those issues will be ignored in the whole
    FOR loop and the whole ``Keyword`` call respectively.

- Ignore unused variables starting with ``_`` (``${_variable}``) ([issue #1457](https://github.com/MarketSquare/robotframework-robocop/issues/1457)

### Fixes

- Fix ``unused-variable`` and ``variable-overwritten-before-usage`` rules not reporting violations in ``TRY`` blocks ([issue #1548](https://github.com/MarketSquare/robotframework-robocop/issues/1548))
- Fix ``wrong-case-in-keyword-call`` rule false positive report on names with ``.`` character with first_word_capitalized = True ([issue #1555](https://github.com/MarketSquare/robotframework-robocop/issues/1555))
- Fix ``wrong-case-in-keyword-name`` rule incorrectly handling names with ``.`` character ([issue #1555](https://github.com/MarketSquare/robotframework-robocop/issues/1555))

### Documentation

- Added documentation linters (with MegaLinter) and fixed several issues in our documentation.

## 6.13.0

### Features

- Add ``per_file_ignores`` option to ignore rules matching file patterns ([issue #1134](https://github.com/MarketSquare/robotframework-robocop/issues/1134))

Example configuration:

```toml
[tool.robocop.lint.per_file_ignores]
"test.robot" = ["VAR02"]
"ignore_subdir/*" = ["empty-line-after-section", "DOC01"]
"ignore_file_in_subpath/test2.robot" = ["SPC10"]
```

- Allow manually disabling reports with ``enabled=False``. It can be used to disable default ``print_issues`` report ([issue #1540](https://github.com/MarketSquare/robotframework-robocop/issues/1540))
- Add ``docs_url`` property to rule class which points to rule documentation URL ([issue #1432](https://github.com/MarketSquare/robotframework-robocop/issues/1432))

### Fixes

- Fix piping output (``robocop check > output.txt``) not working on Windows because of code lines converted to emojis ([issue #1539](https://github.com/MarketSquare/robotframework-robocop/issues/1539))
- Fix configuration file loaded from the root directory with ``--ignore-file-config`` option enabled (other configuration files were correctly ignored)

### Documentation

- Describe how to extend the Robocop Rule class using ``docs_url`` as an example ([here](https://robocop.dev/stable/linter/custom_rules/#change-rule-class-behaviour)).

## 6.12.0

### Features

- Add ``extends`` configuration parameter which allows inheriting configuration from another file ([issue #1453](https://github.com/MarketSquare/robotframework-robocop/issues/1453))
- Change ``mixed-tabs-and-spaces`` (SPC06) rule behaviour to report all occurrences of mixed tabs and spaces in a file ([issue #848](https://github.com/MarketSquare/robotframework-robocop/issues/848))
-  ``format_files`` (robocop API entrypoint for formatting files) now accepts ``return_result`` parameter for returning exit code instead of raising SystemExit
- ``RenameVariables`` not longer replaces spaces in variable names with the math operators ([issue #1428](https://github.com/MarketSquare/robotframework-robocop/issues/1428))

### Fixes

- Fix ``AlignKeywordsSection`` and ``AlignTestCasesSection`` not aligning VAR variables ([issue #1493](https://github.com/MarketSquare/robotframework-robocop/issues/1493))
- Fix optional ``no-embedded-keyword-arguments`` rule fatal exception when reading a file with invalid syntax
- Fix the empty configuration file causing Robocop to fail ([issue #1536](https://github.com/MarketSquare/robotframework-robocop/issues/1536))

### Documentation

- Add ``deprecated names`` section to all the rules that list previous names and ids of the rule

## 6.11.0

### Features

- Add ``--silent`` option to disable all output when running Robocop ([issue #1512](https://github.com/MarketSquare/robotframework-robocop/issues/1512))
- Improve startup performance of the Robocop (using a Robocop repository as a benchmark: from 5s to 0.3s). It was done
  by fixing issues in handling ignored files and by properly caching configuration files (to avoid multiple lookups).
  The difference may be noticeable only for the large, complex projects ([issue #1503](https://github.com/MarketSquare/robotframework-robocop/issues/1503))

### Fixes

- Fix directories from the ``.gitignore`` file not ignored ([issue #1503](https://github.com/MarketSquare/robotframework-robocop/issues/1503))
- Fix ``migrate`` command migrating formatters with ``enabled=False`` from the old transform to select option ([issue #1492](https://github.com/MarketSquare/robotframework-robocop/issues/1492))
- Fix ``migrate`` command not splitting multiline configurations ([issue #1491](https://github.com/MarketSquare/robotframework-robocop/issues/1491))
- Fix multiline inline IF splitting. To avoid issues when formatting such code, **all inline IFs are now flattened to a single line** ([issue #1506](https://github.com/MarketSquare/robotframework-robocop/issues/1506)):

```robotframework
*** Test Cases ***
Multiline inline IF
    IF    True
    ...    Something
```

becomes:

```robotframework
*** Test Cases ***
Multiline inline IF
    IF    True    Something
```
- Fix ``enabled`` formatter parameter not validating as a boolean ([issue #1476](https://github.com/MarketSquare/robotframework-robocop/issues/1476))

### Documentation

- Mark disabled rules in the documentation (previously they were not distinguishable from the enabled rules) ([issue #1518](https://github.com/MarketSquare/robotframework-robocop/issues/1518))
- Add two new sections to the documentation:
  - [Python API Reference](https://robocop.dev/stable/user_guide/python_api/)
  - [AI integration](https://robocop.dev/stable//integrations/ai/)

## 6.10.1

### Fixes

- Fix ``verbose``, ``force_exclude`` and ``skip_gitignore`` options not supported in the configuration file

### Documentation

- Fix incorrect code examples in the documentation.

## 6.10.0

### Documentation

Release a new documentation website.

Rewrite of our documentation from Sphinx to MkDocs, now hosted at https://robocop.dev.

## 6.9.2

### Fixes

- Fix invalid Robot Framework dependency version range

## 6.9.1

### Fixes

- Fix invalid rule positions stopping Sonar Qube import ([issue #1417](https://github.com/MarketSquare/robotframework-robocop/issues/1417))
End-to-end testing of Sonar Qube issue imports revealed multiple problems with diagnostic positioning.
All problematic rules included an incorrect offset of 1. The following rules have been corrected:

- ``invalid-setting-in-resource`` (ERR16)
- ``unreachable-code`` (MISC10)
- ``keyword-name-is-reserved-word`` (NAME03)
- ``invalid-section`` (NAME16)

## 6.9.0

### Documentation

Rule documentation now contains information about deprecated names. It is especially helpful during migration to
Robocop 6.0 or comparing results between old and new Robocop reports.

## 6.8.3

### Fixes

- Fix Robocop failing to scan directory with dangling symlink ([issue #1494](https://github.com/MarketSquare/robotframework-robocop/issues/1494))

Robocop should be able to scan a directory with dangling (pointing to a non-existing path) symlink.

## 6.8.2

### Fixes

- Fix comment handling in Set Variable If with ReplaceWithVAR formatter ([issue #1495](https://github.com/MarketSquare/robotframework-robocop/issues/1495))

``ReplaceWithVAR`` no longer abruptly stops when converting ``Set Variable If`` with comments to ``VAR``.

## 6.8.1

### Fixes

- Fix Python 3.14 compatibility issues, where Robocop disabled 1/3 of the rules.

## 6.8.0

### Features

- Add a new rule: unused disabler rule ([issue #1312](https://github.com/MarketSquare/robotframework-robocop/issues/1312))

A new rule ``unused-disabler`` (MISC15) has been added to detect Robocop disabler directives (such as ``# noqa`` or
``# robocop: off``) that are not being used. This typically occurs when:

- A code violation is fixed, but the disabler is not removed
- A rule is disabled globally, making local disablers redundant
- Multiple overlapping disablers are present

- Improved comment handling in SplitTooLongLine formatter ([issue #1444](https://github.com/MarketSquare/robotframework-robocop/issues/1444))

The ``SplitTooLongLine`` formatter now has better comment handling.

**Previous behavior:**

When formatting keyword call or ``VAR`` by ``SplitTooLongLine`` formatter, comments were moved above the statement,
for example:

```
Long Keyword That Will Be Split    multiple   args  # comment
```

Was formatted to:

```
# comment
Long Keyword That Will Be Split
...    multiple
...    args
```

This caused unindented effect where robocop disabler directives (e.g. ``# robocop: off``) were also moved above the
statement and no longer applied correctly.

**New behavior:**

Comments are now kept on the first line of the split statement:

```
Long Keyword That Will Be Split  # comment
...    multiple
...    args
```

This ensures that disablers and other comments remain associated with the correct statement.

- Disablers are discoverable anywhere in comments

Disabler directives can now be placed anywhere within a comment, not just at the beginning.

**Previous behavior:**

Only the first disabler at the start of a comment was recognised:

```
# only robocop: off=some-rule is recognized
Keyword Call  # robocop: off=some-rule robocop: fmt: off

# only noqa is recognized
Keyword Call  # noqa robocop fmt: off

# nothing is recognized
Keyword Call  # TODO: robocop: off
```

**New behavior:**

All disablers are now recognised regardless of their position in the comment. Additionally, the syntax is more
flexible and rules can be separated by commas with or without spaces:

```
# Both formats are now valid:
# robocop: off=rule1,rule2
# robocop: off=rule1, rule2
```

### Fixes

- Fix overwrite mode not working from the configuration file ([issue #1478](https://github.com/MarketSquare/robotframework-robocop/issues/1478))

Fixed an issue where the ``overwrite`` mode was not being applied when specified in the configuration file. The
following configuration now works correctly:

```toml
[tool.robocop.format]
overwrite = false
```

- Fix rules url pointing to a non-existing location ([issue #1481](https://github.com/MarketSquare/robotframework-robocop/issues/1481))

Rules urls (such as SARIF helpUri, or diagnostic message urls) were pointing to non-existent locations after a
documentation refactor. URLs now correctly point to:

https://robocop.readthedocs.io/en/v{version}/rules/rules_list.html#{rule-name} .

- Fix line too long rule reporting lines with new disablers

New disabler directives (``robocop: fmt: off`` and ``fmt: off``) were not ignored by ``line-too-long`` rule.

From now on, together with other disablers, comments with disablers will be ignored when checking line length.

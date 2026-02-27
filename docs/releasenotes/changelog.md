# Release notes

# [8.0.0](https://github.com/MarketSquare/robotframework-robocop/compare/v7.2.0...v8.0.0) (2026-02-11)

More detailed notes regarding 8.0.0 [here](8.0.0.md).

### Breaking changes

* dropped support for Python 3.9
* dropped support for Robot Framework 4
* Deprecated ``deprecated-statement`` rule
* Deprecated ``ReplaceReturns`` formatter
* Deprecated ``AddMissingEnd`` formatter
* refactored source files handling with common ``SourceFile`` class
* redesigned configuration layer for typing safety and OOP friendliness

### Features

* Fixable rules (#1617) (128c849)
* deprecate ``deprecated-statement`` rule and split into new rules
* new rule DEPR08 ``deprecated-run-keyword-if``
* new rule DEPR09 ``deprecated-loop-keyword``
* new rule DEPR10 ``deprecated-return-keyword`` (with a fix)
* new rule DEPR11 ``deprecated-return-setting`` (with a fix)
* Robocop is now more verbose
* Keyword naming rules and formatters quotation handling
* performance improvements (#1611) (eea1c56)
* ``report()`` can be now used from the rule class (#1644) (8aff795)
* Robocop is now fully typed (#1661) (42045dc)
* list rules can now return the result when used from the Python (#1629) (457d135)
* MCP is now aware of local config (#1673) (55e18b6)
* Skip documentation by default in NormalizeSeparators (#1672) (5b1ae35)
* Added or improved support for variable type conversion (#1654) (#1650) (#1651) (#1652) #1653)
* New rule ANN04 ``set-keyword-with-type``
* Add ``case_normalization`` parameter to enforce case by RenameKeywords (#1667) (49a0b02)

### Bug fixes

* add explicit typing-extensions dependency (#1680) (b406f25)
* Fix #1174 expression-can-be-simplified raised for == 0 (#1649) (d0f4985)
* Fix #1422 - ReplaceWithVAR formatter replacing variables with item access (#1648) (a9c3377)
* Fix caching the issues with fixes (#1623) (256874b)
* Fix extend-select matching only on rule id, not on rule name (#1669) (403ff7d)
* Fix format --extend-select not enabling formatters (#1668) (3c76c50)
* Fix not all issue format parameters supported by extended output (#1624) (727c38d)
* Fix too-long-variable-name throwing exception on Set X Variable without arguments (#1675) (3a55663)
* multiple paths passed to robocop check/format command resolving to the same config (#1614) (bdcfd48)
* Fix rst-style urls in the documentation (#1640) (eb1dcab)
* Update RenameVariables formatter so it treats numbers as part of word and does not split on it (#1663) (eddfd96)

## [8.2.1](https://github.com/MarketSquare/robotframework-robocop/compare/v8.2.0...v8.2.1) (2026-02-27)


### Bug Fixes

* Fix circular import error due to ConfigManager split from config.py ([#1695](https://github.com/MarketSquare/robotframework-robocop/issues/1695)) ([09e3fda](https://github.com/MarketSquare/robotframework-robocop/commit/09e3fdaa8e83a16b19f49c5f199f728d056fde27))

## [8.2.0](https://github.com/MarketSquare/robotframework-robocop/compare/v8.1.1...v8.2.0) (2026-02-22)


### Features

* **mcp:** Allow to pass configuration file path via MCP tools ([#1691](https://github.com/MarketSquare/robotframework-robocop/issues/1691)) ([da5dc6e](https://github.com/MarketSquare/robotframework-robocop/commit/da5dc6e04cda7764608fd10abf4e9e7574836a2e))

## [8.1.1](https://github.com/MarketSquare/robotframework-robocop/compare/v8.1.0...v8.1.1) (2026-02-20)


### Bug Fixes

* Fix unused-variable reported on variable names starting with digit ([#1689](https://github.com/MarketSquare/robotframework-robocop/issues/1689)) ([fc6b78d](https://github.com/MarketSquare/robotframework-robocop/commit/fc6b78de9faa3d61acc0a6e9f8424c0cc4333efa))

## [8.1.0](https://github.com/MarketSquare/robotframework-robocop/compare/v8.0.0...v8.1.0) (2026-02-19)


### Features

* Replace `typer-slim` with `typer` ([#1685](https://github.com/MarketSquare/robotframework-robocop/issues/1685)) ([b83400f](https://github.com/MarketSquare/robotframework-robocop/commit/b83400f5727d4a4b82092319401abdf7fba699e8))


### Bug Fixes

* unused-argument rule raised when argument is used in item access or inline eval ([#1687](https://github.com/MarketSquare/robotframework-robocop/issues/1687)) ([d014a53](https://github.com/MarketSquare/robotframework-robocop/commit/d014a53d32b9effe696fccc993f675efb3724941))

## [7.2.0](https://github.com/MarketSquare/robotframework-robocop/compare/v7.1.0...v7.2.0) (2026-01-01)


### Features

* **mcp:** add new tools and improve UX for large codebases ([#1601](https://github.com/MarketSquare/robotframework-robocop/issues/1601)) ([9b1d871](https://github.com/MarketSquare/robotframework-robocop/commit/9b1d871a2c40549de1d2f1b707201da47f6c68a6))
* **mcp:** add response caching and error handling middleware ([#1599](https://github.com/MarketSquare/robotframework-robocop/issues/1599)) ([406cfbe](https://github.com/MarketSquare/robotframework-robocop/commit/406cfbefaa229664fdd39e5265f2f47958aabb64))
* **mcp:** enhance MCP server with batch operations, quality metrics, and improved LLM guidance ([#1593](https://github.com/MarketSquare/robotframework-robocop/issues/1593)) ([c6a853b](https://github.com/MarketSquare/robotframework-robocop/commit/c6a853bd016eff8f65742c79c511fd8712abc1a3))
* Refactor print_issues report to gain 3x perfomance gain on printing ([#1605](https://github.com/MarketSquare/robotframework-robocop/issues/1605)) ([6755d96](https://github.com/MarketSquare/robotframework-robocop/commit/6755d96ceadb0b78a80f6e70e5e262967029fde3))


### Bug Fixes

* **caching:** Fix CLI always overriding cache=true/false in the configuration file ([#1608](https://github.com/MarketSquare/robotframework-robocop/issues/1608)) ([b31a5ef](https://github.com/MarketSquare/robotframework-robocop/commit/b31a5ef95c1d706623656aa3f1417730f8c23034))
* **release:** fix triggering Github workflows from automated scripts ([#1594](https://github.com/MarketSquare/robotframework-robocop/issues/1594)) ([72ce0ff](https://github.com/MarketSquare/robotframework-robocop/commit/72ce0ff36aed05eef362aa0aeed80324b2ec7a8e))

## [7.1.0](https://github.com/MarketSquare/robotframework-robocop/compare/v7.0.0...v7.1.0) (2025-12-23)


### Features

* add commented-out-code detection rule (COM06) ([#1564](https://github.com/MarketSquare/robotframework-robocop/issues/1564)) ([8afa9d2](https://github.com/MarketSquare/robotframework-robocop/commit/8afa9d268d4ca909cf56225992962c39a088f8bf))
* add file-level caching for linter and formatter to skip unchanged files ([#1565](https://github.com/MarketSquare/robotframework-robocop/issues/1565)) ([ceb02cc](https://github.com/MarketSquare/robotframework-robocop/commit/ceb02ccff7cf5316ef8debb5040bfa625981eba0))
* add MCP server for AI assistant integration ([#1583](https://github.com/MarketSquare/robotframework-robocop/issues/1583)) ([c68330a](https://github.com/MarketSquare/robotframework-robocop/commit/c68330a34a740e86388ee540327ed6f1d1fe83fb))
* add three separate rules for variable type annotations (RF 7.3+) ([#1579](https://github.com/MarketSquare/robotframework-robocop/issues/1579)) ([03ef483](https://github.com/MarketSquare/robotframework-robocop/commit/03ef483446a153137035c48f8f6e63ce02cca480))
* automate release process with release-please ([#1571](https://github.com/MarketSquare/robotframework-robocop/issues/1571)) ([4bd6d3f](https://github.com/MarketSquare/robotframework-robocop/commit/4bd6d3f5cddaa4c85085ca87b8960720e77d8dd6))
* **VAR02:** add ignore parameter for unused-variable rule ([#1576](https://github.com/MarketSquare/robotframework-robocop/issues/1576)) ([0c2ebf4](https://github.com/MarketSquare/robotframework-robocop/commit/0c2ebf41a2f43f0cb73e586b3e254c02cdfacf7c))


### Bug Fixes

* Invalid Robocop disabler accepted as disabler for all rules ([#1569](https://github.com/MarketSquare/robotframework-robocop/issues/1569)) ([595ffdb](https://github.com/MarketSquare/robotframework-robocop/commit/595ffdb83a3b50ccebf4883493b221076782836b))
* **mcp:** fix limit handling bugs and add enhancements ([#1589](https://github.com/MarketSquare/robotframework-robocop/issues/1589)) ([0926a4d](https://github.com/MarketSquare/robotframework-robocop/commit/0926a4d114b10bdb8a468a472f1105d9a227c645))


### Documentation

* add annotations rule group to documentation ([#1439](https://github.com/MarketSquare/robotframework-robocop/issues/1439)) ([#1588](https://github.com/MarketSquare/robotframework-robocop/issues/1588)) ([50cbfa7](https://github.com/MarketSquare/robotframework-robocop/commit/50cbfa72cd34997ce0a63aeaaa5e109a05f83bb6))
* Add caching documentation ([#1572](https://github.com/MarketSquare/robotframework-robocop/issues/1572)) ([5d941e8](https://github.com/MarketSquare/robotframework-robocop/commit/5d941e849f5ac84a8208b1d21ccdf861006b4cbc))

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

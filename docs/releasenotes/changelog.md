# Release notes

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

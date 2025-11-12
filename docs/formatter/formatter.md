# Formatter

Format your Robot Framework code by running:

```bash
robocop format
```

It will recursively discover all ``*.robot`` and ``*.resource`` files in the current directory.

You can also use a specific path or paths:

```bash
robocop format file.robot resources/etc test.robot
```

Robocop will also find and skip paths from `.gitignore` files. It is possible to configure how Robocop discovers
files using various options (see [file discovery](../user_guide/intro.md#file-discovery)).

## Formatter selection

Robocop can be configured to run only selected formatters. You can see what rules are currently enabled by running:

```bash
robocop list formatters
```

The following options can be used to select rules:

- ``--select`` (see [configuration reference](../configuration/configuration_reference.md#select_1)) to only run selected formatters
- ``--custom-formatters`` (see [configuration reference](../configuration/configuration_reference.md#custom-formatters)) to load custom formatters

It is also possible to disable rules not available in the selected Robot Framework version using [target version](../configuration/configuration_reference.md#target-version).

Rules can be also disabled in the code using [disablers](../configuration/disablers.md) directives.

## Displaying the difference

If you want to see which lines are changed by tool add ``--diff`` flag:

```bash
robocop format --diff test.robot
--- test.robot before
+++ test.robot after
@@ -1,23 +1,15 @@
 *** Test Cases ***
Simple IF
-    IF    $condition1
-        Keyword    argument
-    END
-    IF    $condition2
-        RETURN
-    END
+    IF    $condition1    Keyword    argument
+    IF    $condition2    RETURN
```

The difference is colorized by default (green for added and red for removed lines). You can disable this behaviour with
``color`` option:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --diff --no-color
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    diff = true
    color = false
    ``` 

## File write mode

Pass ``--no-overwrite`` flag to not modify the files when running the `Robocop`. Combine it with ``--diff`` to run
a preview of how files will look after formatting:

```bash
robocop format --no-overwrite test.robot
```

## Status code

By default `Robocop` returns ``0`` exit code after successful run and 1 if there was an error. You can make `Robocop`
exit ``1`` if any file would be formatted by passing ``--check``. By default, files will not be formatted (same as
running with ``--no-overwrite``):

```bash
robocop format --check golden.robot
0
robocop format --check ugly.robot
1
```

If you want `Robocop` to format the files while using ``--check`` flag, add ``--overwrite``:

```bash
robocop format --check --overwrite file.robot
```

## Formatter configuration

Formatters that support configuration can be configured using [``--configure``](../configuration/configuration_reference.md#configure)
option.

## List of formatters

To see the list of formatters included with `Robocop` use ``robocop list formatters``:

```bash
> robocop list formatters
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Name                       ┃ Enabled ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ AddMissingEnd              │ Yes     │
│ NormalizeSeparators        │ Yes     │
│ DiscardEmptySections       │ Yes     │
│ MergeAndOrderSections      │ Yes     │
│ RemoveEmptySettings        │ Yes     │
│ ReplaceEmptyValues         │ Yes     │
│ ReplaceWithVAR             │ No      │
│ NormalizeAssignments       │ Yes     │
│ GenerateDocumentation      │ No      │
│ OrderSettings              │ Yes     │
│ OrderSettingsSection       │ Yes     │
│ NormalizeTags              │ Yes     │
│ OrderTags                  │ No      │
│ RenameVariables            │ No      │
│ IndentNestedKeywords       │ No      │
│ AlignSettingsSection       │ Yes     │
│ AlignVariablesSection      │ Yes     │
│ AlignTemplatedTestCases    │ No      │
│ AlignTestCasesSection      │ No      │
│ AlignKeywordsSection       │ No      │
│ NormalizeNewLines          │ Yes     │
│ NormalizeSectionHeaderName │ Yes     │
│ NormalizeSettingName       │ Yes     │
│ ReplaceRunKeywordIf        │ Yes     │
│ SplitTooLongLine           │ Yes     │
│ SmartSortKeywords          │ No      │
│ RenameTestCases            │ No      │
│ RenameKeywords             │ No      │
│ ReplaceReturns             │ Yes     │
│ ReplaceBreakContinue       │ Yes     │
│ InlineIf                   │ Yes     │
│ Translate                  │ No      │
│ NormalizeComments          │ Yes     │
└────────────────────────────┴─────────┘
To see detailed docs run:
    robocop docs formatter_name
Non-default formatters needs to be selected explicitly with --select or configured with param `enabled=True`.
```

You can display short documentation on particular formatter with ``docs formatter`` command:

```bash
> robocop docs DiscardEmptySections
Formatter DiscardEmptySections:

Remove empty sections.

Sections are considered empty if there are only empty lines inside.
You can remove sections with only comments by setting the `` allow_only_comments `` parameter to False:

```robotframework
*** Variables ***
# this section will be removed with the `` allow_only_comments `` parameter set to False

See https://robocop.dev/stable/formatters/formatters_list/DiscardEmptySections.html for more examples.
```

## Line endings

See [line endings](../configuration/configuration_reference.md#line-ending) for details how to configure line endings.

## Rerun the formatting in place

Because of the high independence of each formatter, Robocop runs them in specific order to obtain predictable results.
But sometimes the subsequent formatter modifies the file to the point that it requires another run of the Robocop.
A good example would be one formatter that replaces the deprecated syntax, but a new syntax is inserted using standard
whitespace. If there is formatter that aligns this whitespace according to special rules
(like ``AlignKeywordsSection``) we need to run Robocop again to format this whitespace.

This could be inconvenient in some cases where the user had to rerun Robocop without knowing why. That's why Robocop
now has the option ``--reruns`` that allows to define limit of how many extra reruns Robocop can perform if the
file keeps changing after the formatting. The default is ``0``. Recommended value is ``3``
although in the vast majority of cases one extra run should suffice (and only in cases described above).

See [reruns](../configuration/configuration_reference.md#reruns) for details how to configure reruns.

Note that if you enable it, it can double the execution time of Robocop (if the file was modified, it will be
formatted again to check if the next formatting does not further modify the file).

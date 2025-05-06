.. _formatter:

*********
Formatter
*********

Format your Robot Framework code by running:

..  code-block:: none

    robocop format

It will recursively discover all ``*.robot`` and ``*.resource`` files in the current directory.

You can also use path specific path or paths:

..  code-block:: none

    robocop format file.robot resources/etc test.robot

Robocop will also find and skip paths from `.gitignore` files. It is possible to configure how Robocop discover
files using various options - see :ref:`file_discovery`.

Displaying the difference
--------------------------
If you want to see which lines are changed by tool add ``--diff`` flag:

..  code-block:: none

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

Difference is colorized by default (green for added and red for removed lines). You can disable this behaviour with
``color`` option:

.. tab-set::

    .. tab-item:: Cli

        .. code:: shell

             robocop format --diff --no-color

    .. tab-item:: Configuration file

        .. code:: toml

            [tool.robocop.format]
            diff = true
            color = false

File write mode
---------------
Pass ``--no-overwrite`` flag to not modify the files when running the `Robocop`. Combine it with ``--diff`` to run a preview
of how files will look after formatting:

..  code-block:: none

    robocop format --no-overwrite test.robot

Status code
------------
By default `Robocop` returns 0 exit code after successful run and 1 if there was an error. You can make `Robocop` exit 1
if any file would be transformed by passing ``--check``. By default files will not be transformed (same as running with
``--no-overwrite``):

..  code-block:: none

    robocop format --check golden.robot
    0
    robocop format --check ugly.robot
    1

If you want `Robocop` to transform the files while using ``--check`` flag add ``--overwrite``:

..  code-block:: none

    robocop format --check --overwrite file.robot

Configuration
--------------
See :ref:`configuration` for information how to configure `Robocop`.

List of formatters
-------------------

To see list of formatters included with `Robocop` use ``robocop list formatters``::

    > robocop list formatters
                   Formatters
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

FIXME
Pass optional value ``enabled`` or ``disabled`` to filter out output by the status of the formatter::

    > robocop list formatters --filter disabled
                    Transformers
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
    ┃ Name                    ┃ Enabled ┃
    ┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
    │ OrderTags               │ No      │
    │ IndentNestedKeywords    │ No      │
    │ AlignTemplatedTestCases │ No      │
    │ AlignTestCasesSection   │ No      │
    │ AlignKeywordsSection    │ No      │
    │ SmartSortKeywords       │ No      │
    │ RenameTestCases         │ No      │
    │ RenameKeywords          │ No      │
    │ Translate               │ No      │
    └─────────────────────────┴─────────┘
    (...)


You can display short documentation on particular transformer with ``docs formatter``::

    > robocop docs DiscardEmptySections
    Formatter DiscardEmptySections:

    Remove empty sections.
    Sections are considered empty if there are only empty lines inside.
    You can remove sections with only comments by setting 'allow_only_comments' parameter to False:

        *** Variables ***
        # this section will be removed with'alow_only_comments' parameter set to False

    Supports global formatting params: '--start-line' and '--end-line'.

    See https://robocop.readthedocs.io/en/stable/formatters/formatters_list/DiscardEmptySections.html for more examples.

Format selected lines
---------------------

Most formatters support running `Robocop` only on selected lines. Use ``--start-line`` and ``--end-line`` for this::

    robocop format --start-line 5 --end-line 10 file.robot

If you want to disable formatting in particular files see disablers section in :ref:`configuration`.  # TODO

Line endings
----------------

When working on multiple platforms the file can contain different line endings (``CRLF``, ``LF``). By default
Robocop will replace all line endings with system native line ending. It may be problematic if you're using
different platforms. You can force specific line ending or autodetect line ending used in the file and use it by
configuring ``--line-ending`` option:

- native:  use operating system's native line endings (default)
- windows: use Windows line endings (CRLF)
- unix:    use Unix line endings (LF)
- auto:    maintain existing line endings (uses what's used in the first line of the file)

Rerun the formatting in place
------------------------------

Because of high independence of each formatter, Robocop runs them in specific order to obtain predictable results.
But sometimes the subsequent formatter modifies the file to the point that it requires another run of Robocop.
Good example would be one formatter that replaces the deprecated syntax - but new syntax is inserted using standard
whitespace. If there is transformer that aligns this whitespace according to special rules
(like ``AlignKeywordsSection``) we need to run Robocop again to format this whitespace.

This could be inconvenient in some cases where user had to rerun Robocop without knowing why. That's why Robocop
now has option ``--reruns`` that allows to define limit of how many extra reruns Robocop can perform if the
file keeps changing after the transformation. The default is ``0``. Recommended value is ``3``
although in vast majority of cases one extra run should suffice (and only in cases described above).

Example usage:

..  code-block:: none

    > robocop format --reruns 3 --diff test.robot

Note that if you enable it, it can double the execution time of Robocop (if the file was modified, it will be
formatted again to check if next formatting does not further modify the file).

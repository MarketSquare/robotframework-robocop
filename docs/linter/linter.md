# Linter

Lint your Robot Framework code by running:

```bash
robocop check
```

It will recursively discover all ``*.robot`` and ``*.resource`` files in the current directory.

You can also use a specific path or paths:

```bash
robocop check file.robot resources/etc test.robot
```

Robocop will also find and skip paths from `.gitignore` files. It is possible to configure how Robocop discovers
files using various options (see [file discovery](../user_guide/intro.md#file-discovery)).

An example of the output the tool can produce:

```bash
resources\operations.resource:15:5 VAR02 Variable '${var}' is assigned but not used
    |
 13 |
 14 | Connect To Database
 15 |     ${conn}    Setup Connection
    |     ^^^^^^ VAR02
    |

tests\payments.robot:38:1 DEPR02 'Force Tags' is deprecated since Robot Framework version 6.0, use 'Test Tags' instead
    |
 36 | Metadata       Version     ${VERSION}
 37 | Suite Setup    Setup Payments
 38 | Force Tags     smoke    payments
    | ^^^^^^^^^^ DEPR02
    |
```

It is also possible to produce simple or grouped output (see [print_issues](../linter/reports/print_issues.md)).

## Rule selection

Robocop can be configured to run only selected rules. You can see what rules are currently enabled by running:

```bash
robocop list rules
```

The following options can be used to select rules:

- ``--select`` (see [configuration reference](../configuration/configuration_reference.md#select)) to only run selected rules
- ``--ignore`` (see [configuration reference](../configuration/configuration_reference.md#ignore)) to ignore and disabled rules
- ``--threshold`` (see [configuration reference](../configuration/configuration_reference.md#threshold)) to filter rules below a severity threshold
- ``--custom-rules`` (see [configuration reference](../configuration/configuration_reference.md#custom-rules)) to load custom rules

It is also possible to disable rules not available in the selected Robot Framework version using [target version](../configuration/configuration_reference.md#target-version).

Rules can be also disabled in the code using [disablers](../configuration/disablers.md) directives.

## Reports

Robocop can generate reports in various formats, both as printed output and formatted files. By default, it uses
``print_issues`` default report to output found issues. You can configure it or enable more reports using
[ the reports](../linter/reports/reports.md) option.

## Rule configuration

Rules and reports that support configuration can be configured using [``--configure``](../configuration/configuration_reference.md#configure)
option.

## Language support

Robot Framework 6.0 added support for Robot settings and headers translation. 

Robocop will automatically detect the language of the source code if it contains a language header:

```robotframework
Language: Finnish

*** Asetukset ***
Dokumentaatio        Example using Finnish.
```

If the file does not contain a language header, ``--language`` option can be used to specify the language:

Robocop will not recognise translated
names unless it is properly configured. You can supply language code or name in the configuration using
``--language`` option (see [configuration reference](../configuration/configuration_reference.md#language)).

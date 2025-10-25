# Robocop

Robocop is a tool that performs static code analysis and formatting of [Robot Framework](https://github.com/robotframework/robotframework>)
code.

It uses official [Robot Framework parsing API](https://robot-framework.readthedocs.io/en/stable) to parse files and runs
a number of checks, looking for potential errors or violations to code quality standards (commonly referred as a
*linting issues*). It can also format code to ensure a consistent code style.

<div class="grid cards" markdown>

-   :book:{ .lg .middle } __Starting guide__

    ---

    See how to install and use Robocop

    [:octicons-arrow-right-24: User Guide](user_guide/intro.md)

-   :material-file-cog-outline:{ .lg .middle } __Configuration__

    ---

    Configure Robocop to your needs

    [:octicons-arrow-right-24: Configuration](configuration/index.md)

-   :material-format-list-text:{ .lg .middle } __Linter__

    ---

    View the list of available linter rules

    [:octicons-arrow-right-24: Rules list](rules_list.md)

-   :material-broom:{ .lg .middle } __Formatter__

    ---

    View the list of available formatters

    [:octicons-arrow-right-24: Formatters list](formatter/formatters/AddMissingEnd.md)

</div>

## Installation

```bash
pip install robotframework-robocop
```

## Usage

Lint the Robot Framework files with:

```bash
robocop check
```

Example output:

```bash
> robocop check --report rules_by_error_type test.robot

test.robot:26:13 DEPR02 'Continue For Loop' is deprecated since Robot Framework version 5.*, use 'CONTINUE' instead
    |
 24 |     FOR    ${var}  IN RANGE  10
 25 |         WHILE    $var
 26 |             Continue For Loop
    |             ^^^^^^^^^^^^^^^^^ DEPR02
 27 |             Continue For Loop If  $var > 10
 28 |             Exit For Loop If  $var < 0
    |

test.robot:28:1 SPC14 Variable in Variables section is not left aligned
   |
 1 | *** Variables ***
 2 | ${VAR} 1
 3 |  ${VAR}  1
   | ^ SPC14
 4 |   ${VAR}  1
 5 | VALUE  1

Found 2 issues: 1 ERRORs, 1 WARNINGs, 0 INFO.
```

Format the Robot Framework files with:

```bash
robocop format
```

# Embedded Robot Framework code

Robocop can lint and format Robot Framework code that is embedded in other files:

- **Markdown** files (`.md`, `.markdown`) – fenced code blocks tagged with ` ```robotframework ` (or ` ```robot `).
- **Python** files (`.py`) – the same fenced blocks placed inside docstrings, as used for runnable examples in
  library documentation.

This mirrors the embedded execution support that Robot Framework added in version 7.5, but Robocop does its own
parsing, so it works regardless of the installed Robot Framework version.

A single file may contain zero, one, or many code blocks. **Each block is treated as an independent suite** – it is
linted and formatted on its own, and the surrounding prose, fences and indentation are left untouched.

````markdown
# Example

Some documentation describing the test below.

```robotframework
*** Test Cases ***
Example Test
    Log    message
```
````

## Opting in

Embedded files are **not** analyzed by default. There are two ways to opt in:

1. **Pass the file directly** on the command line:

    ```bash
    robocop check docs/example.md
    robocop format library.py
    ```

2. **Add the extension to the include patterns** so the files are picked up during directory scans:

    ```bash
    robocop check --include "*.md" --include "*.py" .
    ```

    or in the configuration file:

    ```toml
    [tool.robocop]
    include = ["*.robot", "*.resource", "*.md"]
    ```

## Positions and fixes

Reported issues point at the **exact physical line and column** of the code inside the original file, not at a
position within an extracted block. Automatic fixes (`--fix`) and formatting are written back in place, preserving
the block indentation (for example the indentation of a fenced block inside a Python docstring) and the file's line
endings.

## Notes

- Because every block is an independent suite, suite-level rules (such as *missing documentation in suite*) are
  reported once per block.
- Blocks tagged with any language other than `robotframework`/`robot` are ignored.

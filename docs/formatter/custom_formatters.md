# Custom formatters

## How to include custom formatters

``--custom-formatters`` option allows including custom formatters. It can point to a single file (named the same as
the formatter class) or to a module containing multiple formatters. Each formatter must be a class that inherits from
`robocop.formatter.formatters.Formatter` class.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --custom-formatters CustomFormatters --custom-formatters CustomFormatter.py
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    custom_formatters = [
        "CustomFormatters",
        "CustomFormatter.py"
    ]
    ```

It is also possible to include custom formatters using [select](../configuration/configuration_reference.md#select_1)
option. Select loads only selected formatters, while ``--custom-formatters`` load custom formatters after loading
default formatters.

## How to write custom formatters

Custom formatter should inherit from `robocop.formatter.formatters.Formatter` class. This class is Robocop's
wrapper around ``ModelTransformer`` class from the Robot Framework. This is a special visitor class, which visits
all ast nodes in the Robot Framework model and allows modifying it.

First, you need to define a formatter class:

```python
from robocop.formatter.formatters import Formatter


class YourCustomFormatter(Formatter):
    """This formatter will remove tests with the word "deprecated" in the test case name."""
    def visit_TestCase(self, node):
        if 'deprecated' in node.name:
            return None
        return node
```

When you define visitor class, you overwrite the one inherited from ``ModelTransformer`` grandparent class.
You can modify the node, add new nodes, or remove nodes. If the visitor returns ``None``, the node is removed from
the model. Refer to the Robocop source code for more examples.

## Custom formatter modules

Importing formatters from a module works similarly to how custom libraries are imported in Robot Framework.
If the file has the same name as the formatter, it will be auto-imported. For example, the following import:

```bash
robocop format --custom-formatters CustomFormatter.py
```

will auto import class ``CustomFormatter`` from the file.

If the file does not contain a class with the same name, it is a directory, or it is a Python module with
``__init__.py`` file, the Robocop will import multiple formatters. Formatters are executed in the order they are
imported.


Following ``__init__.py``:

```python
from robocop.formatter.formatters import Formatter

from other_file import FormatterB


class FormatterA(Formatter):
    ...
```

will import FormatterB and FormatterA and execute them in this order.

If you want to use different order, you can define the FORMATTERS list in the file:

```python
FORMATTERS = [
    "FormatterA",
    "FormatterB"
]
```

# OrderSettingsSection

Order settings inside ``*** Settings ***`` section.

{{ configure_hint("OrderSettingsSection") }}

Settings are grouped in the following groups:

- documentation (Documentation, Metadata),
- imports (Library, Resource, Variables),
- settings (Suite Setup and Teardown, Test Setup and Teardown, Test Timeout, Test Template),
- tags (Force Tags, Default Tags)

Then ordered by groups (according to ``group_order = documentation,imports,settings,tags`` order). Every
group is separated by ``new_lines_between_groups = 1`` new lines.
Settings are ordered inside a group. The default order can be modified through the following parameters:

- ``documentation_order = documentation,metadata``
- ``imports_order = preserved`` (default, see [imports order](#imports-order) section to how configure it)
- ``settings_order = suite_setup,suite_teardown,test_setup,test_teardown,test_timeout,test_template``

=== "Before"

    ```robotframework
    *** Settings ***
    Metadata  value  param

    Force Tags  tag
    ...  tag

    Documentation  doc  # this is comment
    ...  another line
    Test Timeout  1min

    # I want to be keep together with Test Setup

    Test Setup  Keyword


    Suite Setup  Keyword
    Default Tags  1
    Suite Teardown  Keyword2

    Variables   variables.py
    Library  Stuff
    Library  Collections
    Resource    robot.resource
    Library  stuff.py  WITH NAME  alias
    ```

=== "After"

    ```robotframework
    *** Settings ***
    Documentation  doc  # this is comment
    ...  another line
    Metadata  value  param

    Variables   variables.py
    Library  Stuff
    Library  Collections
    Resource    robot.resource
    Library  stuff.py  WITH NAME  alias

    Suite Setup  Keyword
    Suite Teardown  Keyword2
    # I want to be keep together with Test Setup
    Test Setup  Keyword
    Test Timeout  1min

    Force Tags  tag
    ...  tag
    Default Tags  1
    ```

Using the same example with non-default group order, we will move tags from end to beginning of the section:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure OrderSettingsSection.group_order=tags,documentation,imports,settings
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "OrderSettingsSection.group_order=tags,documentation,imports,settings"
    ]
    ```

will result in:

=== "Before"

    ```robotframework
    *** Settings ***
    Metadata  value  param

    Force Tags  tag
    ...  tag

    Documentation  doc  # this is comment
    ...  another line
    Test Timeout  1min

    # I want to be keep together with Test Setup

    Test Setup  Keyword


    Suite Setup  Keyword
    Default Tags  1
    Suite Teardown  Keyword2
    ```

=== "After"

    ```robotframework
    *** Settings ***
    Force Tags  tag
    ...  tag
    Default Tags  1

    Documentation  doc  # this is comment
    ...  another line
    Metadata  value  param

    Suite Setup  Keyword
    Suite Teardown  Keyword2
    # I want to be keep together with Test Setup
    Test Setup  Keyword
    Test Timeout  1min
    ```

## Settings order

The order of settings inside a common group can also be changed:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure OrderSettingsSection.settings_order=suite_teardown,suite_setup,test_setup,test_teardown,test_timeout,test_template
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "OrderSettingsSection.settings_order=suite_teardown,suite_setup,test_setup,test_teardown,test_timeout,test_template"
    ]
    ```

will result in:

=== "Default order"

    ```robotframework
    *** Settings ***
    Suite Setup    Suite Setup Keyword
    Suite Teardown    Suite Teardown Keyword
    Test Timeout    1min
    ```

=== "Configured order"

    ```robotframework
    *** Settings ***
    Suite Teardown    Suite Teardown Keyword
    Suite Setup    Suite Setup Keyword
    Test Timeout    1min
    ```

## Preserve order

If you want to preserve order of the settings inside the group you can use ``preserved`` value:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure OrderSettingsSection.settings_order=preserved --configure OrderSettingsSection.documentation_order=preserved
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "OrderSettingsSection.settings_order=preserved",
        "OrderSettingsSection.documentation_order=preserved"
    ]
    ```


Imports are preserved by default.

## Imports order

By default, the order of the imports is preserved. You can overwrite this behaviour:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure OrderSettingsSection.imports_order=library,resource,variables
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "OrderSettingsSection.imports_order=library,resource,variables"
    ]
    ```

With preceding configuration `robocop format` will put library imports first, then resources and variables last.
Builtin library imports are moved to the top and sorted alphabetically.

Example:

=== "Before"

    ```robotframework
    *** Settings ***
    Suite Teardown  Keyword2

    Variables   variables.py
    Library  Stuff
    Library  Collections
    Resource    robot.resource
    Library   ABC
    ```

=== "After"

    ```robotframework
    *** Settings ***
    Library  Collections
    Library  Stuff
    Library   ABC
    Resource    robot.resource
    Variables   variables.py

    Suite Teardown  Keyword2
    ```

## Removing settings

Setting names omitted from custom order will be removed from the file. In the following example we are missing metadata,
therefore all metadata will be removed:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure OrderSettingsSection.documentation_order=documentation
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "OrderSettingsSection.documentation_order=documentation"
    ]
    ```

## Empty lines between group of settings

Group of settings are separated by ``new_lines_between_groups = 1`` new lines. It can be configured:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure OrderSettingsSection.new_lines_between_groups=2
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "OrderSettingsSection.new_lines_between_groups=2"
    ]
    ```

will result in:

=== "Before"

    ```robotframework
    *** Settings ***
    Library  Collections
    Default Tags    tag
    Documentation  doc  # this is comment
    ...  another line
    Metadata  value  param
    ```

=== "Default separator"

    ```robotframework
    *** Settings ***
    Documentation  doc  # this is comment
    ...  another line
    Metadata  value  param

    Library  Collections

    Default Tags    tag
    ```

=== "0"

    ```robotframework
    *** Settings ***
    Documentation  doc  # this is comment
    ...  another line
    Metadata  value  param
    Library  Collections
    Default Tags    tag
    ```

=== "2"

    ```robotframework
    *** Settings ***
    Documentation  doc  # this is comment
    ...  another line
    Metadata  value  param


    Library  Collections


    Default Tags    tag
    ```

If you're not preserving the default order of libraries, they will be grouped into built-in libraries and custom libraries.
Parsing errors (such as Resources instead of Resource, duplicated settings) are moved to the end of a section.

=== "Before"

    ```
    *** Settings ***
    Test Templating  Template  # parsing error
    Library  Stuff
    Resource    robot.resource
    Library  Dialogs  # built in library
    ```

=== "After"

    ```
    *** Settings ***
    Library  Dialogs  # built in library
    Library  Stuff
    Resource    robot.resource

    Test Templating  Template  # parsing error
    ```

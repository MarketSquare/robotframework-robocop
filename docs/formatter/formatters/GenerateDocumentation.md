# GenerateDocumentation

Generate keyword documentation with the documentation template.

{{ enable_hint("GenerateDocumentation") }}

By default, GenerateDocumentation uses
[Google docstring](https://google.github.io/styleguide/pyguide.html#383-functions-and-methods)
as the documentation template.

=== "Before"

    ```robotframework
    *** Keywords ***
    Keyword
        [Arguments]    ${arg}
        ${var}   ${var2}    Step
        RETURN    ${var}    ${var2}
    
    Keyword With ${embedded} Variable
        Step
    ```

=== "After"

    ```robotframework
    *** Keywords ***
    Keyword
        [Documentation]
        ...
        ...    Arguments:
        ...        ${arg}:
        ...
        ...    Returns:
        ...        ${var}
        ...        ${var2}
        [Arguments]    ${arg}
        ${var}   ${var2}    Step
        RETURN    ${var}    ${var2}
    
    Keyword With ${embedded} Variable
        [Documentation]
        ...
        ...    Arguments:
        ...        ${embedded}:
        Step
    ```

## Overwriting documentation

The documentation will not be added if it is already present in the keyword. You can configure it by using
``overwrite`` parameter:

=== "Before"

    ```robotframework
    *** Keywords ***
    Keyword With Documentation
        [Documentation]    Short description.
        [Arguments]    ${arg}
        Step
    ```

=== "After (overwrite = False)"

    ```robotframework
    *** Keywords ***
    Keyword With Documentation
        [Documentation]    Short description.
        [Arguments]    ${arg}
        Step
    ```

=== "After (overwrite = True)"

    ```robotframework
    *** Keywords ***
    Keyword With Documentation
        [Documentation]
        ...    Arguments:
        ...        ${arg}:
        [Arguments]    ${arg}
        Step
    ```

## Custom template

Custom templates can be loaded from the file using ``doc_template`` parameter. If you pass
``google`` string it will use default template:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select GenerateDocumentation --configure GenerateDocumentation.doc_template=google
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "GenerateDocumentation"
    ]
    configure = [
        "GenerateDocumentation.doc_template=google"
    ]
    ```

Templates support [Jinja templating engine](https://jinja.palletsprojects.com/) and we are providing several variables
based on the keyword data. Here is the default template:

```jinja
{% raw %}
{% if keyword.arguments|length > 0 %}
{{ formatting.cont_indent }}Args:
{%- for arg in keyword.arguments %}
{{ formatting.cont_indent }}{{ formatting.cont_indent }}{{ arg.name }}: {% endfor %}
{% endif -%}
{% if keyword.returns|length > 0 %}
{{ formatting.cont_indent }}Returns:
{%- for value in keyword.returns %}
{{ formatting.cont_indent }}{{ formatting.cont_indent }}{{ value }}: {% endfor %}
{% endif -%}
{% endraw %}
```

The Jinja syntax is described [here](https://jinja.palletsprojects.com/en/3.1.x/templates/). You can use it as
a reference to create your own template. The following subsections explain in detail possible features.

Path to template can be absolute or relative (to working directory or configuration file directory):

=== ":octicons-command-palette-24: absolute path"

    ```bash
    robocop format --select GenerateDocumentation --configure GenerateDocumentation.doc_template="C:/doc_templates/template.jinja"
    ```

=== ":material-file-cog-outline: absolute path"

    ```toml
    [tool.robocop.format]
    select = [
        "GenerateDocumentation"
    ]
    configure = [
        "GenerateDocumentation.doc_template='C:/doc_templates/template.jinja'"
    ]
    ```

=== ":octicons-command-palette-24: relative path"

    ```bash
    robocop format --select GenerateDocumentation --configure GenerateDocumentation.doc_template="template.jinja"
    ```

=== ":material-file-cog-outline: relative path"

    ```toml
    [tool.robocop.format]
    select = [
        "GenerateDocumentation"
    ]
    configure = [
        "GenerateDocumentation.doc_template='template.jinja'"
    ]
    ```

### First line of the documentation

The first line of the template is also the first line of the documentation that goes next to the ``[Documentation]``
setting.

=== "Template"

    ```text
      First line of template
      Second line of example
    Third line.
    ```

=== "Generated example"

    ```robotframework
    *** Keywords ***
    Keyword
        [Documentation]    First line of template
        ...    Second line of example
        ...  Third line.
        Step
    ```

Leave the first line empty in the template if you want to start documentation from the second line.

### Whitespace can be static or dynamic

Any whitespace in the template will apply to the documentation. For example you can put 4 spaces after every argument
and before `->` sign:

=== "Template"

    ```jinja
    {% raw %}
    Args:
    {%- for arg in keyword.arguments %}
            {{ arg.name }}    ->{% endfor %}
    {% endraw %}
    ```

=== "Code"

    ```robotframework
    *** Keywords ***
    Keyword
        [Arguments]    ${arguments}    ${arg}    ${arg2}
        Step
    ```

=== "Generated example"

    ```robotframework
    *** Keywords ***
    Keyword
        [Documentation]
        ...    Args:
        ...        ${arguments}    ->
        ...        ${arg}    ->
        ...        ${arg2}    ->
        [Arguments]    ${arguments}    ${arg}    ${arg2}
        Step
    ```

Robocop provides also ``formatting`` class that contains two variables:

- ``separator`` (default 4 spaces) - spacing between tokens
- ``cont_indent`` (default 4 spaces) - spacing after ``...`` signs

When used in the template, these variables will reflect the values defined in your configuration:

```jinja
{% raw %}
{{ formatting.separator }}
{{ formatting.cont_indent }}
{% endraw %}
```

### Arguments data

Robocop provides arguments as a list of variables in ``keyword.arguments`` variable. Every argument contains the following
variables:

 - ``name`` - name of the argument without default value (i.e. ``${arg}``)
 - ``default`` - default value (i.e. ``value``)
 - ``full_name`` - name with default value (i.e. ``${arg} = value``)

You can use them in the template:

=== "Template"

    ```jinja
    {% raw %}
    Arguments:
    {%- for arg in keyword.arguments %}
        {{ arg.name }} - {{ arg.default }}:{% endfor %}
    {% endraw %}
    ```

=== "Code"

    ```robotframework
    *** Keywords ***
    Keyword
        [Arguments]    ${var}    ${var2} = 2
        Step
    ```

=== "Generated example"

    ```robotframework
    *** Keywords ***
    Keyword
        [Documentation]
        ...    Arguments:
        ...        ${var} - :
        ...        ${var2} - 2:
        [Arguments]    ${var}    ${var2} = 2
        Step
    ```

You can take advantage of Jinja templating features such as ``if`` blocks. For instance, to include an ``=`` between
the argument name and its default value only when the default value is not empty, you can use:

```jinja
{% raw %}
{{ arg.name }}{% if arg.default %} = '{{ arg.default }}'{% endif %}
{% endraw %}
```

### Returned values data

Returned values are provided as a list of variables names in ``keyword.returns`` variable.

=== "Template"

    ```jinja
    {% raw %}
    Returns:
    {%- for value in keyword.returns %}
        {{ value }}:{% endfor %}
    {% endraw %}
    ```

=== "Code"

    ```robotframework
    *** Keywords ***
    Keyword
        ${value}    Step
        RETURN    ${value}
    ```

=== "Generated example"

    ```robotframework
    *** Keywords ***
    Keyword
        [Documentation]
        ...    Returns:
        ...        ${value}:
        ${value}    Step
        RETURN    ${value}
    ```

### Keyword name

You can add current keyword name to the documentation using ``keyword.name`` variable.

=== "Template"

    ```jinja
    {% raw %}
    This is documentation for '{{ keyword.name }}' keyword.
    {% endraw %}
    ```

=== "Code"

    ```robotframework
    *** Keywords ***
    Keyword
        Step
    
    Other Keyword
        Step 2
    ```

=== "Generated example"

    ```robotframework
    *** Keywords ***
    Keyword
        [Documentation]    This is documentation for 'Keyword' keyword.
        Step
    
    Other Keyword
        [Documentation]    This is documentation for 'Other Keyword' keyword.
        Step 2
    ```

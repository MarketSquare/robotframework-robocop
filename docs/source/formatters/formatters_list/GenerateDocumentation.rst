.. _GenerateDocumentation:

GenerateDocumentation
================================

Generate keyword documentation with the documentation template.

.. |FORMATTERNAME| replace:: GenerateDocumentation
.. include:: disabled_hint.txt


By default, GenerateDocumentation uses
`Google docstring <https://google.github.io/styleguide/pyguide.html#383-functions-and-methods>`_
as the documentation template.

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Keywords ***
            Keyword
                [Arguments]    ${arg}
                ${var}   ${var2}    Step
                RETURN    ${var}    ${var2}

            Keyword With ${embedded} Variable
                Step

    .. tab-item:: After

        .. code:: robotframework

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

Overwriting documentation
--------------------------

The documentation will not be added if it is already present in the keyword. You can configure it
by using ``overwrite`` parameter:

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Keywords ***
            Keyword With Documentation
                [Documentation]    Short description.
                [Arguments]    ${arg}
                Step

    .. tab-item:: After (overwrite = False)

        .. code:: robotframework

            *** Keywords ***
            Keyword With Documentation
                [Documentation]    Short description.
                [Arguments]    ${arg}
                Step

    .. tab-item:: After (overwrite = True)

        .. code:: robotframework

            *** Keywords ***
            Keyword With Documentation
                [Documentation]
                ...    Arguments:
                ...        ${arg}:
                [Arguments]    ${arg}
                Step

Custom template
----------------

Custom templates can be loaded from the file using ``doc_template`` parameter. If you pass
``google`` string it will use default template::

    > robocop format --configure GenerateDocumentation.doc_template=google

Templates support `Jinja templating engine <https://jinja.palletsprojects.com/>`_ and we are providing several variables
based on the keyword data. Below, there is a default template:

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

The Jinja syntax is described `here <https://jinja.palletsprojects.com/en/3.1.x/templates/>`_. You can use it as
a reference to create your own template. The following subsections explain in detail possible features.

Path to template can be absolute or relative (to working directory or configuration file directory)::

    > robocop format --configure GenerateDocumentation.doc_template="C:/doc_templates/template.jinja"
    > robocop format --configure GenerateDocumentation.doc_template="template.jinja"

.. dropdown:: First line of the documentation

    The first line of the template is also the first line of the documentation that goes next to the ``[Documentation]`` setting.

    .. tab-set::

        .. tab-item:: Template

            .. code:: text

                    First line of template
                    Second line of example
                  Third line.

        .. tab-item:: Generated example

            .. code:: robotframework

                *** Keywords ***
                Keyword
                    [Documentation]    First line of template
                    ...    Second line of example
                    ...  Third line.
                    Step

    Leave the first line empty in the template if you want to start documentation from the second line.

.. dropdown:: Whitespace can be static or dynamic

    Any whitespace in the template will apply to the documentation. For example you can put 4 spaces after every argument
    and before `->` sign:

    .. tab-set::

        .. tab-item:: Template

            .. code:: text

                Args:
                {%- for arg in keyword.arguments %}
                        {{ arg.name }}    ->{% endfor %}

        .. tab-item:: Code

            .. code:: robotframework

                *** Keywords ***
                Keyword
                    [Arguments]    ${arguments}    ${arg}    ${arg2}
                    Step

        .. tab-item:: Generated example

            .. code:: robotframework

                *** Keywords ***
                Keyword
                    [Documentation]
                    ...    Args:
                    ...        ${arguments}    ->
                    ...        ${arg}    ->
                    ...        ${arg2}    ->
                    [Arguments]    ${arguments}    ${arg}    ${arg2}
                    Step

    Robotidy provides also ``formatting`` class that contains two variables:

    - ``separator`` (default 4 spaces) - spacing between tokens
    - ``cont_indent`` (default 4 spaces) - spacing after ``...`` signs

    You can use them in the template - and their values will be affected by your configuration::

        {{ formatting.separator }}
        {{ formatting.cont_indent }}

.. dropdown:: Arguments data

    Robotidy provides arguments as a list of variables in ``keyword.arguments`` variable. Every argument contains the following
    variables:

     - ``name`` - name of the argument without default value (ie. ``${arg}``)
     - ``default`` - default value (ie. ``value``)
     - ``full_name`` - name with default value (ie. ``${arg} = value``)

    You can use them in the template:

    .. tab-set::

        .. tab-item:: Template

            .. code:: text

                Arguments:
                {%- for arg in keyword.arguments %}
                    {{ arg.name }} - {{ arg.default }}:{% endfor %}

        .. tab-item:: Code

            .. code:: robotframework

                *** Keywords ***
                Keyword
                    [Arguments]    ${var}    ${var2} = 2
                    Step

        .. tab-item:: Generated example

            .. code:: robotframework

                *** Keywords ***
                Keyword
                    [Documentation]
                    ...    Arguments:
                    ...        ${var} - :
                    ...        ${var2} - 2:
                    [Arguments]    ${var}    ${var2} = 2
                    Step

    Note that you can use Jinja templating features like ``if`` blocks. For example, if you want to put ``=`` between
    the argument name and default value (only if default value is not empty), you can use::

    {{ arg.name }}{% if arg.default %} = '{{ arg.default }}'{% endif %}

.. dropdown:: Returned values data

    Returned values are provided as a list of variables names in ``keyword.returns`` variable.

    .. tab-set::

        .. tab-item:: Template

            .. code:: text

                Returns:
                {%- for value in keyword.returns %}
                    {{ value }}:{% endfor %}

        .. tab-item:: Code

            .. code:: robotframework

                *** Keywords ***
                Keyword
                    ${value}    Step
                    RETURN    ${value}

        .. tab-item:: Generated example

            .. code:: robotframework

                *** Keywords ***
                Keyword
                    [Documentation]
                    ...    Returns:
                    ...        ${value}:
                    ${value}    Step
                    RETURN    ${value}

.. dropdown:: Keyword name

    You can add current keyword name to the documentation using ``keyword.name`` variable.

    .. tab-set::

        .. tab-item:: Template

            .. code:: text

                    This is documentation for '{{ keyword.name }}' keyword.

        .. tab-item:: Code

            .. code:: robotframework

                *** Keywords ***
                Keyword
                    Step

                Other Keyword
                    Step 2

        .. tab-item:: Generated example

            .. code:: robotframework

                *** Keywords ***
                Keyword
                    [Documentation]    This is documentation for 'Keyword' keyword.
                    Step

                Other Keyword
                    [Documentation]    This is documentation for 'Other Keyword' keyword.
                    Step 2

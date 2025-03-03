.. _rules:

***********
Rule basics
***********

Checkers
========

# TODO: cli / configuration files examples

.. automodule:: robocop.linter.rules

.. _list-rules:

List available rules
--------------------

To get list of available rules (with enabled/disabled status) use ``list rules`` command:

..  code-block:: none

    > robocop list rules
    Rule - ARG01 [W]: unused-argument: Keyword argument '{name}' is not used (enabled)
    Rule - ARG02 [W]: argument-overwritten-before-usage: Keyword argument '{name}' is overwritten before usage (enabled)
    Rule - ARG03 [E]: undefined-argument-default: Undefined argument default, use {arg_name}=${{EMPTY}} instead (enabled)
    (...)

Rules list can be filtered out by glob pattern:

..  code-block:: none

    > robocop list rules --pattern tag*
    Rule - TAG01 [W]: tag-with-space: Tag '{tag}' contains spaces (enabled)
    Rule - TAG02 [I]: tag-with-or-and: Tag '{tag}' with reserved word OR/AND (enabled)
    Rule - TAG03 [W]: tag-with-reserved-word: Tag '{tag}' prefixed with reserved word `robot:` (enabled)
    Rule - TAG06 [I]: tag-already-set-in-test-tags: Tag '{tag}' is already set by {test_force_tags} in suite settings (enabled)
    Rule - TAG11 [I]: tag-already-set-in-keyword-tags: Tag '{tag}' is already set by {keyword_tags} in suite settings (enabled)


To list only enabled or disabled rules:

..  code-block:: none

    > robocop list rules --pattern tag-with* --filter ENABLED
    Rule - TAG01 [W]: tag-with-space: Tag '{tag}' contains spaces (enabled)
    Rule - TAG02 [I]: tag-with-or-and: Tag '{tag}' with reserved word OR/AND (enabled)
    Rule - TAG03 [W]: tag-with-reserved-word: Tag '{tag}' prefixed with reserved word `robot:` (enabled)

    > robocop list rules --pattern non-builtin-imports-not-sorted --filter DISABLED
    Rule - IMP03 [W]: non-builtin-imports-not-sorted: Non builtin library import '{custom_import}' should be placed before '{previous_custom_import}' (disabled)

Available list filters::

    DEFAULT - no pattern specified, print all default rules (enabled and disabled)
    ENABLED - print only enabled rules
    DISABLED - print only disabled rules
    DEPRECATED - print only deprecated rules

Rule message
============

# .. automodule:: robocop.rules

# .. module:: robocop

.. _rule-severity:

Rule severity
=============

.. automodule:: robocop.linter.rules.RuleSeverity

.. _severity-threshold:

Severity threshold
-------------------

Selected rules can be configured to have different severity depending on the parameter value.

Using ``line-too-long`` as an example - this rule issues a warning when line length exceeds configured value
(default ``120``).
It is possible to configure this rule to issue a warning for line length above 120 but an error for line length
above 200.
We can use ``severity_threshold`` for this purpose:

.. tab-set::

    .. tab-item:: Cli

        .. code:: shell

            robocop check -c line-too-long.severity_threshold=warning=120:error=200

    .. tab-item:: Configuration file

        .. code:: toml

            [robocop.lint]
            configure = [
                "line-too-long.severity_threshold=warning=120:error=200"
            ]

It supports all default severity values:

- error, e
- warning, w
- info, i

The issue needs to be raised in order for severity thresholds to be evaluated. That's why the parameter value needs to
be configured to raise an issue for at least one of our threshold ranges. In previous example, if we want to issue
info message if the line is longer than 80 characters, we need to configure ``line_length`` parameter
(default ``120``) to 80 to trigger the rule:

.. tab-set::

    .. tab-item:: Cli

        .. code:: shell

            robocop check -c line-too-long.line_length=80 -c line-too-long.severity_threshold=info=80:warning=120:error=200

    .. tab-item:: Configuration file

        .. code:: toml

            [robocop.lint]
            configure = [
                "line-too-long.line_length=80",
                "line-too-long.severity_threshold=info=80:warning=120:error=200"
            ]

Following rules support ``severity_threshold``:

{% for checker_group in checker_groups %}
{% for rule_doc in checker_group[1] %}
{%- if rule_doc.severity_threshold is not none %}
- :ref:`{{ rule_doc.name }}`
{% endif %}
{% endfor %}
{% endfor %}

.. _selecting-rules:

Selecting and ignoring rules
=============================

You can select or ignore particular rules using rule name or id.

To only select and run ``missing-doc-keyword`` rule:

.. tab-set::

    .. tab-item:: Cli

        .. code:: shell

            robocop check --select missing-doc-keyword

    .. tab-item:: Configuration file

        .. code:: toml

            [robocop.lint]
            select = [
                "missing-doc-keyword"
            ]

To run all rules except ``missing-doc-keyword`` rule:

.. tab-set::

    .. tab-item:: Cli

        .. code:: shell

            robocop check --ignore missing-doc-keyword

    .. tab-item:: Configuration file

        .. code:: toml

            [robocop.lint]
            ignore = [
                "missing-doc-keyword"
            ]

Robocop supports glob patterns:

.. tab-set::

    .. tab-item:: Cli

        .. code:: shell

             robocop check --select *doc*

    .. tab-item:: Configuration file

        .. code:: toml

            [robocop.lint]
            select = [
                "*doc*"
            ]

All rules will be ignored except those with *doc* in its name (like ``missing-doc-keyword``, ``too-long-doc`` etc).

To configure multiple rules you can repeat option / or add more to array (configuration file):

.. tab-set::

    .. tab-item:: Cli

        .. code:: shell

             robocop check --select rule1 --select rule2 --select rule3 --ignore rule2

    .. tab-item:: Configuration file

        .. code:: toml

            [robocop.lint]
            select = [
                "rule1",
                "rule2",
                "rule3"
            ]
            ignore = [
                "rule2"
            ]

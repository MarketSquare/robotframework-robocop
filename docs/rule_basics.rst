.. _rules:

***********
Rule basics
***********

Checkers
========

.. automodule:: robocop.checkers

.. _listing-rules:

Listing available rules
-----------------------

To get list of available rules (with enabled/disabled status) use ``-l`` / ``--list`` option:

..  code-block:: none

    > robocop --list
    Rule - 0201 [W]: missing-doc-keyword: Missing documentation in '{{ name }}' keyword (enabled)
    Rule - 0202 [W]: missing-doc-test-case: Missing documentation in '{{ name }}' test case (enabled)
    Rule - 0203 [W]: missing-doc-suite: Missing documentation in suite (enabled)
    (...)

If some of the rules are disabled from CLI it will be reflected in the output:

..  code-block:: none

    > robocop --exclude 02* --list
    Rule - 0201 [W]: missing-doc-keyword: Missing documentation in '{{ name }}' keyword (disabled)
    Rule - 0202 [W]: missing-doc-test-case: Missing documentation in '{{ name }}' test case (disabled)
    Rule - 0203 [W]: missing-doc-suite: Missing documentation in suite (disabled)
    Rule - 0301 [W]: not-allowed-char-in-name: Not allowed character '{{ character }}' found in {{ block_name }} name (enabled)
    (...)

Rules list can be filtered out by glob pattern:

..  code-block:: none

    > robocop --list tag*
    Rule - 0601 [W]: tag-with-space: Tag '{{ tag }}' should not contain spaces (enabled)
    Rule - 0602 [I]: tag-with-or-and: Tag '{{ tag }}' with reserved word OR/AND. Hint: make sure to include this tag using lowercase name to avoid issues (enabled)
    Rule - 0603 [W]: tag-with-reserved-word: Tag '{{ tag }}' prefixed with reserved word `robot:` (enabled)
    Rule - 0606 [I]: tag-already-set-in-test-tags: Tag 'mytag' is already set by Test Tags in suite settings (enabled)

Use ``-lc \ --list-configurables`` argument to list rules together with available configurable parameters. Optional pattern argument is also supported:

..  code-block:: none

    robocop --list-configurables empty-lines-between-sections
    Rule - 1003 [W]: empty-lines-between-sections: Invalid number of empty lines between sections ({{ empty_lines }}/{{ allowed_empty_lines }}) (enabled)
        Available configurables for this rule:
            empty_lines = 2
                type: int
                info: number of empty lines required between sections


To list only enabled or disabled rules:

..  code-block:: none

    > robocop -i tag-with* --list ENABLED
    Rule - 0601 [W]: tag-with-space: Tag '{{ tag }}' should not contain spaces (enabled)
    Rule - 0602 [I]: tag-with-or-and: Tag '{{ tag }}' with reserved word OR/AND. Hint: make sure to include this tag using lowercase name to avoid issues (enabled)
    Rule - 0603 [W]: tag-with-reserved-word: Tag '{{ tag }}' prefixed with reserved word `robot:` (enabled)

    > robocop -e inconsistent-assignment-in-variables --list-configurables DISABLED
    Rule - 0910 [W]: inconsistent-assignment-in-variables: The assignment sign is not consistent inside the variables section. Expected '{{ expected_sign }}' but got '{{ actual_sign }}' instead (disabled)
        assignment_sign_type = autodetect
            type: parse_assignment_sign_type
            info: possible values: 'autodetect' (default), 'none' (''), 'equal_sign' ('=') or space_and_equal_sign (' =')

Available list filters::

    DEFAULT - no pattern specified, print all default rules (enabled and disabled)
    ENABLED - print only enabled rules
    DISABLED - print only disabled rules
    COMMUNITY - print only community rules
    DEPRECATED - print only deprecated rules
    ALL - print all default and community rules

Rule message
============

.. automodule:: robocop.rules

.. module:: robocop

.. _rule-severity:

Rule severity
=============

.. automodule:: robocop.rules.RuleSeverity

.. _severity-threshold:

Severity threshold
-------------------

Selected rules can be configured to have different severity depending on the parameter value.

Using ``line-too-long`` as an example - this rule issues a warning when line length exceeds
configured value (default ``120``).
It is possible to configure this rule to issue a warning for line length above 120
but an error for line length above 200.
We can use ``severity_threshold`` for this purpose::

    robocop -c line-too-long:severity_threshold:warning=120:error=200

It supports all default severity values:

- error, e
- warning, w
- info, i

The issue needs to be raised in order for severity thresholds to be evaluated. That's why the parameter value needs to
be configured to raise an issue for at least one of our threshold ranges. In previous example, if we want to issue
info message if the line is longer than 80 characters, we need to configure ``line_length`` parameter
(default ``120``) to 80 to trigger the rule::

    robocop -c line-too-long:line_length:80 -c line-too-long:severity_threshold:info=80:warning=120:error=200

Following rules support ``severity_threshold``:

{% for checker_group in checker_groups %}
{% for rule_doc in checker_group[1] %}
{%- if rule_doc.severity_threshold is not none %}
- :ref:`{{ rule_doc.name }}`
{% endif %}
{% endfor %}
{% endfor %}

.. _including-rules:

Including and excluding rules
==============================

You can include or exclude particular rules using rule name or id.
Rules are matched in similar way how Robot Framework ``include`` / ``exclude`` arguments.

Described examples::

    robocop --include missing-doc-keyword test.robot

All rules will be ignored except ``missing-doc-keyword`` rule::

    robocop --exclude missing-doc-keyword test.robot

Only ``missing-doc-keyword`` rule will be ignored.

Robocop supports glob patterns::

    robocop --include *doc* test.robot

All rules will be ignored except those with *doc* in its name (like ``missing-doc-keyword``, ``too-long-doc`` etc).

You can provide list of rules in comma-separated format or repeat the argument with value::

    robocop --include rule1,rule2,rule3 --exclude rule2  --exclude rule1 test.robot

You can also use short names of options::

    robocop -i rule1 -e rule2 test.robot

.. _rule severity thresholds:

Rule severity thresholds
===========================
Selected rules can be configured to have different severity depending on the parameter value.

Using ``line-too-long`` as an example - this rule issues a warning when line length exceeds
configured value (default ``120``).
It is possible to configure this rule to issue a warning for line length above 120
but an error for line length above 200.
We can use ``severity_threshold`` for this purpose.

::

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

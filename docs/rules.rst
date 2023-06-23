.. _rules:

Rules
========

.. automodule:: robocop.rules

.. module:: robocop

.. automodule:: robocop.checkers

.. autoclass:: robocop.rules.RuleSeverity
   :members:

{% for checker_group in checker_groups %}
{{ checker_group[0] }}
-------------
{% for rule_doc in checker_group[1] %}
.. _{{ rule_doc.name }}:

{{ rule_doc.name }} / {{ rule_doc.severity }}{{ rule_doc.id }}
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*Added in* ``v{{ rule_doc.robocop_version }}``

Supported RF versions: ``{{ rule_doc.version }}``

**Message**:

``{{ rule_doc.msg }}``

{% if rule_doc.docs|length %}

**Documentation**:

{{ rule_doc.docs }}

{% endif %}

{%- if rule_doc.severity_threshold is not none %}

.. admonition:: Severity thresholds
   :class: note

   This rule supports dynamic severity configurable using thresholds (:ref:`rule severity thresholds`).
   Parameter ``{{ rule_doc.severity_threshold.param_name }}`` will be used to determine issue severity depending on the thresholds.

   When configuring thresholds remember to also set ``{{ rule_doc.severity_threshold.param_name }}`` - its value should be lower or
   equal to the lowest value in the threshold.

{% endif %}

**Configurable parameters**:

.. list-table::
  :width: 100%
  :widths: auto
  :header-rows: 1

  * - Name
    - Default value
    - Type
    - Description
{% for rule_param in rule_doc.params %}
  * - ``{{ rule_param.name }}``
    - ``{{ rule_param.default }}``
    - ``{{ rule_param.type }}``
    - {{ rule_param.desc }}
{% endfor %}

{% if not loop.last %}
----
{% endif %}

{% endfor %}


{% endfor %}

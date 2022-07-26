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
{{ rule_doc.name }}
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
  :width: 100%
  :widths: auto
  :header-rows: 1

  * - Severity
    - Rule id
    - Robot Framework version
  * - {{ rule_doc.severity }}
    - {{ rule_doc.id }}
    - {{ rule_doc.version }}

{{ rule_doc.desc }}.

{%- if rule_doc.ext_docs %}
{{ rule_doc.ext_docs }}
{% endif %}

.. list-table:: Configurable parameters
  :width: 100%
  :widths: auto
  :header-rows: 1

  * - Name
    - Default value
    - Type
    - Description
{% for rule_param in rule_doc.params %}
  * - {{ rule_param.name }}
    - {{ rule_param.default }}
    - {{ rule_param.type }}
    - {{ rule_param.desc }}
{% endfor %}


{% endfor %}


{% endfor %}

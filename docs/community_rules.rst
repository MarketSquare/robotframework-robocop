.. _community rules:

********************
Community rules list
********************

Community rules are optional rules that may handle specific issues or offer particular utility with certain limitations.
All community rules are disabled by default and can be enabled by configuring ``enabled`` parameter::

    robocop --configure sleep-keyword-used:enabled:True

or by including rule in ``--include``::

    robocop --include sleep-keyword-used

{% for checker_group in community_checkers %}
.. _{{ checker_group[0] }}:

{{ checker_group[0] }}
----------------------
{% for rule_doc in checker_group[1] %}
.. _{{ rule_doc.name }}:

{{ rule_doc.name }} / {{ rule_doc.severity }}{{ rule_doc.id }}
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

{% if rule_doc.deprecated %}
.. warning::

      Rule is deprecated.
{% endif %}

*Added in* ``v{{ rule_doc.robocop_version }}`` ⦁ *Supported RF versions*: ``{{ rule_doc.version }}``

**Message**:

``{{ rule_doc.msg }}``

{% if rule_doc.docs|length %}

**Documentation**:

.. highlight:: robotframework
   :force:

{{ rule_doc.docs }}

{% endif %}

{%- if rule_doc.severity_threshold is not none %}

.. admonition:: Severity thresholds
   :class: note

   This rule supports dynamic severity configurable using thresholds (:ref:`severity-threshold`).
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

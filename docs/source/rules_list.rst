.. _rules list:

**********
Rules list
**********

This is the complete list of all Robocop rules grouped by categories.
If you want to learn more about the rules and their features, see :ref:`rules`.

There are over a 160 rules available in Robocop and they are organized into the following categories:

# TODO
* 02: :ref:`Documentation`
* 03: :ref:`Naming`
* 04: :ref:`Errors`
* 05: :ref:`Lengths`
* 06: :ref:`Tags`
* 07: :ref:`Comments`
* 08: :ref:`Duplications`
* 09: :ref:`Misc`
* 10: :ref:`Spacing`

Each rule has a unique rule id consisting of:

- a alphanumeric group name (for example ``DOC``)
- a 2-digit rule number (for example ``01``)

Below is the list of all built-in Robocop rules.

{% for checker_group in builtin_checkers %}
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

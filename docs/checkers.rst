.. _checkers:

Checkers
===================
.. module:: robocop

.. automodule:: robocop.checkers

.. autoclass:: robocop.rules.RuleSeverity
   :members:
   :undoc-members:

.. autoclass:: robocop.checkers.VisitorChecker
   :members:
   :no-undoc-members:
   :show-inheritance:

.. autoclass:: robocop.checkers.RawFileChecker
   :members:
   :no-undoc-members:
   :show-inheritance:

{% for checker_group in checker_groups %}
{{ checker_group[0] }}
-------------
{% for rule_doc in checker_group[1] %}
* {{ rule_doc[1] }}

  Defined in ``robocop.checkers.{{ rule_doc[3] }}``

  .. csv-table:: Configurable parameters
     :header: "name", "type"
     :widths: 20, 20
{% for rule_param in rule_doc[2] %}
     "{{ rule_param[0] }}", "{{ rule_param[1] }}"
{% endfor %}


{% endfor %}


{% endfor %}

.. _rules:

Rules
========

.. automodule:: robocop.rules

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

  .. list-table:: Configurable parameters
     :widths: 25 25 25 25
     :header-rows: 1

     * - name
       - type
       - default
       - info
{% for rule_param in rule_doc[2] %}
     * - {{ rule_param[0] }}
       - {{ rule_param[1] }}
       - {{ rule_param[2] }}
       - {{ rule_param[3] }}
{% endfor %}


{% endfor %}


{% endfor %}
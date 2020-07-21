.. _checkers:

Checkers
===================
.. module:: robocop

.. automodule:: robocop.checkers

.. autoclass:: robocop.messages.MessageSeverity
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
{{ checker_group }}
-------------
{% for checker_class in checker_groups[checker_group] %}
.. autoclass:: {{ checker_class[0] }}
   :show-inheritance:

Reports:
{% for rule in checker_class[1] %}
* {{ rule[0] }}

  .. csv-table:: Configurable parameters
     :header: "name", "type"
     :widths: 20, 20
{% for rule_param in rule[1] %}
     "{{ rule_param[0] }}", "{{ rule_param[1] }}"
{% endfor %}

{% endfor %}
{% endfor %}
{% endfor %}
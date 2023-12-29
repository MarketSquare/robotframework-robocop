New community rules
-------------------

Robocop now contains new type of rules: **community rules**. To put it simply, community rule is just rule disabled
by default. However it allows us to add rules that handle specific problems or have certain limitations. Such rules
will not be enabled by default and users will be able to choose to run them or not.

``Community rule`` name originates from our purpose behind this feature - we want users (our community) to more actively
contribute to Robocop rules. If you developed rule for your company that may benefit more people but is not fit for
everyone feel free to add it in our repository.

Existing community rules can be listed with ``COMMUNITY`` or ``ALL`` filters::

    > robocop --list COMMUNITY
    Rule - 10001 [W]: sleep-keyword-used: Sleep keyword with '{{ duration_time }}' sleep time found (disabled)

Those rules can be enabled by configuring ``enabled`` parameter::

    robocop --configure sleep-keyword-used:enabled:True

or by including rule in ``--include``::

    robocop --include sleep-keyword-used

Community rules - or in other words rules disabled by default - are now part of our core code. It is now also
possible to create custom disabled by default rule. If you want to contribute new community rule or create your own
custom rule then <check out this doc page>. # TODO

https://robocop.readthedocs.io/en/stable/external_rules.html#rules-disabled-by-default
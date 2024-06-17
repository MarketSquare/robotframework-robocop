empty-variable can be now disabled for VAR (#1056)
--------------------------------------------------

I0912 ``empty-variable`` received new parameter ``variable_source`` which allows to enable the rule either only for
variables from ```*** Variables ***``` section or only ``VAR`` statements. By default it works on both.

Deprecate unnecessary-string-conversion rule (#986)
----------------------------------------------------

Rule I0923 ``unnecessary-string-conversion`` is now deprecated. It reported multiple false positive issues that lead
to users breaking the code. If the rule was useful in your project and you know its limitations (coming from not knowing
the exact type of the variable in the IF condition) you can reimplement this rule as custom rule in your project.

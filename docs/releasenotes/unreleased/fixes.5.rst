unnecessary-string-conversion should not be raised for environment variables (#952)
-----------------------------------------------------------------------------------

I0923 ``unnecessary-string-conversion`` was raised for all types of variables including environment variables
(``%{ENV_VAR}``). Such variables are always strings and there is no unnecessary string conversion. For that reason
this rule will now ignore environment variables.

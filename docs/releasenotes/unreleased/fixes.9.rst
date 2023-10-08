if-can-be-used and deprecated-statement double reporting on Run Keyword Unless (#945)
-------------------------------------------------------------------------------------

I0908 ``if-can-be-used`` was introduced in Robot Framework 4.0 to suggest replacing ``Run Keyword If`` and
``Run Keyword Unless`` keywords by ``IF``. Since Robot Framework 5.0 W0319 ``deprecated-statement`` started to warn
on the use of those keywords. Because of that there were 2 issues reported starting from Robot Framework 5.0.

``if-can-be-used`` was updated to only report for Robot Framework 4.0 code. Starting from RF version 5.0 only
``deprecated-statement`` will be reported.

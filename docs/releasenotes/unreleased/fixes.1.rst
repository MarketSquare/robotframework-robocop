Invalid links to rules after documentation refactor (#937)
----------------------------------------------------------

Fixed links to our rules after recent documentation refactor:

- issues_to_lsp_diagnostic API method should now point to rules_list.html instead of rules.html
- SARIF reports should now point to rules_list.html instead of rules.html
- rule description now points to valid url

Also, the SARIF reports will now contain explicit Robocop version in the rules url to decrease number of backward
incompatibility issues when using reports from previous versions.

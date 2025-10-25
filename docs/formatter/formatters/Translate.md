# Translate

Translate Robot Framework source files from one or many languages to different one.

???+ note
    Required Robot Framework version: >=6.0

{{ enable_hint("Translate") }}

Example of Robot Framework markers translation:

=== "Before (default English)"

    ```robotframework
    *** Settings ***
    Documentation    Dokumentacja zestawu

    Library    Collections
    Variables    vars.py

    *** Test Cases ***
    Pierwszy test
        [Setup]    Setup Keyword
        Step 1
    ```

=== "After (translated to Polish)"

    ```robotframework
    *** Ustawienia ***
    Documentation    Dokumentacja zestawu

    Biblioteka    Collections
    Zmienne    vars.py

    *** Przypadki Testowe ***
    Pierwszy test
        [Inicjalizacja]    Setup Keyword
        Step 1
    ```

The language can be configured using ``language`` parameter with the language code (default ``en`` - English):

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select Translate --configure Translate.language=se
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "Translate"
    ]
    configure = [
        "Translate.language=se"
    ]
    ```

Since the translation is from one or many languages to one, only one language can be configured.

## Source language

Robocop will translate only markers that can be recognized. If your source file is written in a different language, 
you need to configure Robocop to recognize a given language. See :ref:`language_support` for more details.
The following example configures Robocop to read English, Polish and German languages and translate Robot Framework
markers to Ukrainian:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select Translate -c Translate.language=uk --language pl,de
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    language = ["pl", "de"]
    select = [
        "Translate"
    ]
    configure = [
        "Translate.language=uk"
    ]
    ```

## BDD keywords

BDD keywords are not translated by default. Set ``translate_bdd`` parameter to ``True`` to enable it:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select Translate -c Translate.translate_bdd=True
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "Translate"
    ]
    configure = [
        "Translate.language=de",
        "Translate.translate_bdd=True"
    ]
    ```

Example of BDD keywords translation:

=== "Before (default English)"

    ```robotframework
    *** Test Cases ***
    Test with BDD keywords
        Given login page is open
        When valid username and password are inserted
        And credentials are submitted
        Then welcome page should be open
    ```

=== "After (translated BDD keywords to German)"

    ```robotframework
    *** Testfälle ***
    Test with BDD keywords
        Angenommen login page is open
        Wenn valid username and password are inserted
        Und credentials are submitted
        Dann welcome page should be open
    ```

Some language has more than one alternative to BDD keyword. For example, Polish can use "Kiedy" or "Gdy" when
translating "When" keyword. In this situation Robocop will choose the first one (sorted alphabetically). It can
be overwritten using  ``<bdd_keyword>_alternative`` parameters:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select Translate -c Translate.language=pl -c Translate.translate_bdd=True -c Translate.when_alternative=Gdy
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "Translate"
    ]
    configure = [
        "Translate.language=pl",
        "Translate.translate_bdd=True",
        "Translate.when_alternative=Gdy"
    ]
    ```

## Language headers

Robocop can add or replace existing language header in the files. For example, if you're translating a file
written in German to Swedish, the language header will change from ``language: de`` to ``language: se``.
Translation to English will remove the language header since it's not necessary.
To do this configure ``add_language_header`` parameter to ``True``:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select Translate --language de -c Translate.language=se -c Translate.add_language_header=True
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    language = "de"
    select = [
        "Translate"
    ]
    configure = [
        "Translate.language=se",
        "Translate.add_language_header=True"
    ]
    ```

will result in:

=== "Before (default German)"

    ```robotframework
    # language: de

    *** Testfälle ***
    Test
        Step
    ```

=== "Translated to Swedish"

    ```robotframework
    # language: se

    *** Testfall ***
    Test
        Step
    ```

=== "Translated to English"

    ```robotframework
    *** Test Cases ***
    Test
        Step
    ```

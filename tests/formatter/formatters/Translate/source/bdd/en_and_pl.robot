*** Test Cases ***
Pierwszy test
    Given Strona Do Logowania Jest Otwarta
    When Login I Hasło Są Wprowadzone
    And Nie Ma Błędów
    Then Strona Główna Powinna Się Otworzyć

Do not translate these
    Given
    Keyword
    Multiline
    ...    keyword

Arguments and return values
    ${arg}    When I Have Some    ${arguments}
    ...    ${more_arguments}

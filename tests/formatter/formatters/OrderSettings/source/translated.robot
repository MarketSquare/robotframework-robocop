language: de
*** Kommentare ***
Hallo liebe Teilnehmenden,

Das ist eine Detsche Suite.


*** Einstellungen ***
Bibliothek      String


*** Variablen ***
${Redner}       René Rohner


*** Testfälle ***
Testfall 1
    [Tags]    marker1    marker2
    Sag mal    Hallo
    Log    Bitte das hier auch in die Console    console=Ja
    [Nachbereitung]    Log To Console    Das ist das Ende
    Log To Console    Das ist mitten drin
    [Vorbereitung]    Log To Console    Das ist der Anfang


*** Schlüsselwörter ***
Sag mal
    Log    ${Nachricht}    html=ja
    [Argumente]    ${Nachricht}

*** Test Cases ***
Test
    VaHa_ValmiitTapahtumatTarkista_Osto    ${NIMIKE}    Ostotilaus          ${OSTOTILAUS}       ${MAARA}            ${ALIVARASTO}       varastopaika=${EMPTY}    tilauspvm=${TILAUSPVM}

Test2
    Lava_VastaanottotapahtumatTarkista    ${VASTAANOTTO}                    ${TILAUS_OCC}       ${OSTOTILAUS}       ${LAHETYS}          ${TILAUSPVM}        ${NIMIKE}           ${NIMIKEKUVAUS}

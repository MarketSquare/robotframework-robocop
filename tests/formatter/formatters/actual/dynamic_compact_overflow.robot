*** Test Cases ***
Test compact overflow with compact overflow limit
    # current compact overflow can go over multiple columns, better to be dynamic compact overflow, used ONLY if really makes it more compact from next column already (not ever two columns in a row misaligned from rest)

    # use compact_overflow for TILAUS to "win" one column
    LäVa_VastaanottotapahtumatTarkista    ${VASTAANOTTO}    ${TILAUS}       ${OSTOTILAUS}       ${LÄHETYS}          ${TILAUSPVM}        ${NIMIKE}           ${NIMIKEKUVAUS}
    LäVa_VastaanottotapahtumatTarkista    ${VASTAANOTTO}    ${TILAUS}       ${OSTOTILAUS}       ${LÄHETYS}          ${TILAUSPVM}        ${NIMIKE}           ${NIMIKEKUVAUS}

    # better to fallback to normal overflow in this case if compact overflow is not helping to align next column tighter
    LäVa_VastaanottotapahtumatTarkista    ${VASTAANOTTO_LONGER}             ${TILAUS_OCC}       ${OSTOTILAUS}       ${LÄHETYS}          ${TILAUSPVM}        ${NIMIKE}           ${NIMIKEKUVAUS}
    LäVa_VastaanottotapahtumatTarkista    ${VASTAANOTTO_LONGER}             ${TILAUS_OCC}       ${OSTOTILAUS}       ${LÄHETYS}          ${TILAUSPVM}        ${NIMIKE}           ${NIMIKEKUVAUS}

    # more complex case with two times in same row, first expecting fallback, second normal compact
    LäVa_VastaanottotapahtumatTarkista    ${VASTAANOTTO_LONGER}             ${TILAUS_OCC}       ${OSTOTILAUS}       ${LÄHETYS_LONGERTXT}    ${TILAUSPVM}    ${NIMIKE}           ${NIMIKEKUVAUS}
    LäVa_VastaanottotapahtumatTarkista    ${VASTAANOTTO_LONGER}             ${TILAUS_OCC}       ${OSTOTILAUS}       ${LÄHETYS_LONGERTXT}    ${TILAUSPVM}    ${NIMIKE}           ${NIMIKEKUVAUS}

    LäVa_VastaaShort        ${VASTAANOTTO_MUCHLONGERTX}    ${TILAUS_OCC}    ${OSTOTILAUS}
    LäVa_VastaaShort        ${VASTAANOTTO_MUCHLONGERTX}    ${TILAUS_OCC}    ${OSTOTILAUS}
    LäVa_VastaanottotapahtumatTarkista    ${VASTAANOTTO_LONGER}             ${TILAUS_OCC}       ${OSTOTILAUS}
    LäVa_VastaanottotapahtumatTarkista    ${VASTAANOTTO_LONGER}             ${TILAUS_OCC}       ${OSTOTILAUS}

*** Test Cases ***
Test compact overflow with compact overflow limit = 1
    ${PALAUTUKSENVASTAANOTTO}=                          VaHa_VastaanottoLuo_Palautustilaus      ${NIMIKE}           ${MÄÄRÄ}            ${PALAUTUSTILAUS}    ${ALIVARASTO}

    ${PALAUTUKSENVASTAANOTTO}=                          VaHa_VastaanottoLuo_Palautustilaus      ${NIMIKE}           ${MÄÄRÄ}            ${PALAUTUSTILAUS}    ${ALIVARASTO}

    # once critical issue - even if too long token barely fits in two columns,
    # the next token should start with + 1 column because sep does not fit
    ${OSTOTILAUS}           ${TOIMITUSPÄIVÄ}=           OsTi_OstotilausLuo_Hankintaehdotuksesta                     ${HANKINTAEHDOTUS}    ${TILAUSPVM}

    ${OSTOTILAUS}           ${TOIMITUSPÄIVÄ}=           OsTi_OstotilausLuo_Hankintaehdotuksesta                     ${HANKINTAEHDOTUS}    ${TILAUSPVM}

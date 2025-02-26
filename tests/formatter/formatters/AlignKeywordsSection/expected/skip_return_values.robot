*** Keywords ***
Skip return values
    # single return value case
    ${def_xhrtimeout}=      SetConfig                   XHRTimeout          0s
    ${def_xhrtimeout}=      SetConfig                   XHRTimeout          0s
    ${def_xhrtimeout}=      SetConfig                   XHRTimeout          0s

    ${a}    ${b}=           SomeKeyword                 somevalue
    ${a}    ${b}=           SomeKeyword                 somevalue

    # alignment between return values is left completely as is
    ${TILAUS_OCC}   ${HINTA_YKSI}   ${HINTA_RIVI}   ${HINTA_TILAUS}   ${TILAUSPVM}=             OCC_TilausTee_fi
    ${TILAUS_OCC}    ${HINTA_YKSI}    ${HINTA_RIVI}    ${HINTA_TILAUS}    ${TILAUSPVM}=         OCC_TilausTee_fi

    ${single}
    ...                     Keyword                     Call

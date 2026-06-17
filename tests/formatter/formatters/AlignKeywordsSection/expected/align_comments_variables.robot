*** Variables ***
# ${OCSP_CERT_GOOD}    certificate status is good
# ${OCSP_FAILED}    ocsp check failed, fallback to crl
# ${OCSP_NOT_AVAILABLE}    certificate status is not available
${VARIABLE}    value


*** Keywords ***
Keyword
    # comment               aligned
    Keyword                 arg

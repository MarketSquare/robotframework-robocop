*** Settings ***
| Resource | geist_toucan_keywords.robot


*** Variables ***
| ${max pages}  | 100
| ${geist type} | PDU


*** Test Cases ***
Repeatedly Login And Then Close
| | ${type}= | Convert To Lowercase | ${geist type}
| | @{pages}= | Set Variable If | '${type}'=='pdu' | ${PDU SYSTEM PAGES}
| | @{pages}= | Set Variable If | '${type}'=='env' | ${ALL BB ENV TOUCAN PAGES}
| | Log To Console | \n
| | FOR | ${index} | IN RANGE | ${max pages}
| |     | ${num}= | Generate Random String | 1 | [NUMBERS]
| |     | ${idx}= | Convert To Integer | ${num}
| |     | ${page name}= | Set Variable | ${pages}[${idx}]
| |     | Log To Console | ${page name}
| |     | Login To Toucan App
| |     | Go To Toucan Page | ${page name}
| | [Teardown] | Close Browser

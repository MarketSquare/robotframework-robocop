*** Settings ***
Documentation       this
...                 is documentation for comparison longer longer

Force Tags          tag                         tag2

Suite Setup         Start Session
...                   host=${IPADDRESS}
...                   user=${USERNAME}
...                   password=${PASSWORD}
Suite Teardown      Close Session

Test Setup          Two Arguments One Line
...                   ${arg}                    ${arg2}
...                   ${arg3}
...                   ${arg4}                   ${arg5}

*** Settings ***
Documentation
...            Provides access to all Keywords needed for interaction with Toucan GUI.
...            For more details on what must be set to use this library, see documentation
...
Library        String
Library        Collections
Library        RequestsLibrary
Library        OperatingSystem
Library        SensorSwitchRig
...            gmswRig    001
Library        SeleniumLibrary
...            timeout=${TIMEOUT}
...            implicit_wait=${TIMEOUT}
...            run_on_failure=Capture Page Screenshot
...            screenshot_root_directory=${OUTPUT DIR}
...            WITH NAME    Selenium
Resource       vertiv_parameter_unicode.robot
Resource       vertiv_lol_sensor_rig.robot
Variables      geist_toucan_constants.py

Suite Setup         Start Session
...                 host=${IPADDRESS}
...                 user=${USERNAME}
...                 password=${PASSWORD}
Suite Teardown      Close Session

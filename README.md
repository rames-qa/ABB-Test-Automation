 # ABB Senior Software Engineer - Test Automation Assessment

## Project Overview

This project automates the ThingsBoard IoT monitoring dashboard validation.

Target Application:
https://demo.thingsboard.io

Automation Framework:
- Python
- Pytest
- Playwright
- Requests API Automation


## Automation Coverage

### UI Automation

File:
test_ui_automation.py

Validations:
- Login validation
- Dashboard navigation
- Widget visibility
- Telemetry labels validation
- Real-time data verification
- Screenshot capture


### API Automation

Files:
- test_api_telemetry.py
- test_api_automation.py


Validations:
- JWT authentication
- Device API validation
- Telemetry API validation
- Response schema validation
- Data type validation
- Retry mechanism


## Test Execution

Install dependencies:

pip install -r requirements.txt


Run complete suite:

pytest -v


Generate HTML report:

pytest -v --html=reports/report.html --self-contained-html


## Test Execution Result

Total Tests: 3

Passed: 3

Failed: 0


Execution Time:
29.16 seconds


## Framework Design

The framework follows:

- Pytest Fixtures
- Session based API authentication
- Logging
- Retry mechanism
- Modular test design
- HTML reporting


## Evidence

Execution report:

reports/report.html


Screenshots:

screenshots/


## Author

Ramesh Kumar K

Software Automation  Testing & Verification and Validation Engineer

import logging
import os
import time
from datetime import datetime
import pytest
import requests

# Configuration
BASE_URL = "https://demo.thingsboard.io"
USERNAME = os.getenv("TB_USERNAME")
PASSWORD = os.getenv("TB_PASSWORD")
MAX_RETRIES = 5
RETRY_DELAY = 3
API_TIMEOUT = 10

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


# Authentication Fixture
@pytest.fixture(scope="module")
def api_session():
    if not USERNAME or not PASSWORD:
        pytest.exit(
            "Missing ThingsBoard credentials.\n"
            "Set TB_USERNAME and TB_PASSWORD environment variables."
        )

    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json"
    })

    login_url = f"{BASE_URL}/api/auth/login"
    payload = {"username": USERNAME, "password": PASSWORD}

    logger.info("Authenticating with ThingsBoard at %s", login_url)

    response = session.post(login_url, json=payload, timeout=API_TIMEOUT)

    if response.status_code != 200:
        pytest.fail(
            f"ThingsBoard Login Failed\n"
            f"Username    : {USERNAME}\n"
            f"Status Code : {response.status_code}\n"
            f"Server Response: {response.text}\n"
            "Possible Reasons: Wrong credentials, account not activated, or account disabled."
        )

    token = response.json().get("token")
    session.headers.update({"X-Authorization": f"Bearer {token}"})
    logger.info("Authentication successful")
    return session


# Helper Functions
def get_device(session):
    url = f"{BASE_URL}/api/tenant/devices?pageSize=10&page=0"
    logger.info("Fetching tenant devices...")

    response = session.get(url, timeout=API_TIMEOUT)
    assert response.ok, f"Device API failed: {response.text}"

    devices = response.json().get("data", [])
    assert devices, "No devices found for this tenant account."

    device = devices[0]
    device_id = device["id"]["id"]
    device_name = device.get("name", "Unknown")

    logger.info("Device Name : %s", device_name)
    logger.info("Device ID   : %s", device_id)
    return device_id


def get_telemetry(session, device_id):
    url = f"{BASE_URL}/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries"

    for attempt in range(1, MAX_RETRIES + 1):
        logger.info("Fetching telemetry (Attempt %d/%d)...", attempt, MAX_RETRIES)
        response = session.get(url, timeout=API_TIMEOUT)

        if response.ok:
            telemetry = response.json()
            if telemetry:
                return telemetry

        time.sleep(RETRY_DELAY)

    pytest.fail(f"Telemetry data not received after {MAX_RETRIES} retries.")


# Test Case
@pytest.mark.telemetry
def test_device_telemetry_validation(api_session):
    start_time = time.time()

    # 1. Fetch Device & Telemetry
    device_id = get_device(api_session)
    telemetry = get_telemetry(api_session, device_id)

    execution_time = time.time() - start_time
    logger.info("Execution Time: %.2f seconds", execution_time)

    # 2. Performance Validation
    assert execution_time < 10, "Telemetry response exceeded 10 seconds SLA"

    # 3. Schema & Data Validation
    assert isinstance(telemetry, dict), "Telemetry payload should be a dictionary"

    for metric, values in telemetry.items():
        logger.info("Validating metric: %s", metric)
        assert isinstance(values, list), f"Metric '{metric}' should be a list"
        assert len(values) > 0, f"Metric '{metric}' contains no records"

        latest = values[0]
        assert "ts" in latest, f"Timestamp missing for metric '{metric}'"
        assert "value" in latest, f"Value missing for metric '{metric}'"

        # Validate Timestamp
        timestamp = latest["ts"]
        assert isinstance(timestamp, int), f"Timestamp for '{metric}' is not an int"
        readable_time = datetime.fromtimestamp(timestamp / 1000)
        logger.info("%s latest timestamp: %s", metric, readable_time)

        # Validate Value Numeric Conversion
        try:
            float(latest["value"])
        except (ValueError, TypeError):
            pytest.fail(f"Invalid non-numeric telemetry value for '{metric}': {latest['value']}")

    # 4. Metric Keyword Matching
    available_metrics = [k.lower() for k in telemetry.keys()]
    logger.info("Available Metrics: %s", available_metrics)

    expected_keywords = ["temperature", "humidity", "power"]
    matched_metrics = [
        kw for kw in expected_keywords 
        if any(kw in metric for metric in available_metrics)
    ]

    logger.info("Matched Expected Metrics: %s", matched_metrics)
    if not matched_metrics:
        logger.warning("None of the standard metrics (temperature, humidity, power) were detected.")

    logger.info("ThingsBoard Telemetry API Test Completed Successfully.")

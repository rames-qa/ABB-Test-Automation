import logging
import os
import time
from datetime import datetime

import pytest
import requests

BASE_URL = os.getenv("TB_BASE_URL", "https://eu.thingsboard.cloud")
USERNAME = os.getenv("TB_USERNAME")
PASSWORD = os.getenv("TB_PASSWORD")

MAX_RETRIES = 5
RETRY_DELAY = 3
API_TIMEOUT = 10

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

@pytest.fixture(scope="module")
def api_session():
    if not USERNAME or not PASSWORD:
        pytest.fail(
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

    logger.info("Authenticating ThingsBoard: %s", login_url)
    response = session.post(login_url, json=payload, timeout=API_TIMEOUT)

    assert response.status_code == 200, (
        f"Login failed\nStatus: {response.status_code}\nResponse: {response.text}"
    )

    token = response.json().get("token")
    assert token, "JWT token not received"

    session.headers.update({"X-Authorization": f"Bearer {token}"})
    logger.info("Authentication successful")
    return session

def get_device(session):
    url = f"{BASE_URL}/api/tenant/devices?pageSize=10&page=0"
    logger.info("Fetching devices")

    response = session.get(url, timeout=API_TIMEOUT)
    assert response.status_code == 200, f"Device API failed: {response.text}"

    devices = response.json().get("data", [])
    assert devices, "No devices found"

    device = devices[0]
    device_id = device["id"]["id"]

    logger.info("Device Name: %s", device.get("name"))
    logger.info("Device ID: %s", device_id)
    return device_id

def get_telemetry(session, device_id):
    url = f"{BASE_URL}/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries"

    for attempt in range(1, MAX_RETRIES + 1):
        logger.info("Telemetry polling attempt %s/%s", attempt, MAX_RETRIES)
        response = session.get(url, timeout=API_TIMEOUT)

        if response.status_code == 200:
            telemetry = response.json()
            if telemetry:
                return telemetry

        time.sleep(RETRY_DELAY)

    pytest.fail("Telemetry data not received")

@pytest.mark.telemetry
def test_device_telemetry_validation(api_session):
    start_time = time.time()

    device_id = get_device(api_session)
    telemetry = get_telemetry(api_session, device_id)

    execution_time = time.time() - start_time
    logger.info("Execution Time: %.2f seconds", execution_time)

    assert execution_time < 10, "Telemetry response exceeded SLA"
    assert isinstance(telemetry, dict)
    logger.info("Telemetry Keys: %s", list(telemetry.keys()))

    for metric, values in telemetry.items():
        assert isinstance(values, list)
        assert values, f"No values found for {metric}"

        latest = values[0]
        assert "ts" in latest
        assert "value" in latest

        timestamp = latest["ts"]
        assert isinstance(timestamp, int)

        readable_time = datetime.fromtimestamp(timestamp / 1000)
        logger.info("%s latest timestamp: %s", metric, readable_time)

        try:
            float(latest["value"])
        except (ValueError, TypeError):
            pytest.fail(f"Invalid value for {metric}")

    logger.info("Telemetry validation completed successfully")

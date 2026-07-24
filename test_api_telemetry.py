import time
import requests
import pytest

BASE_URL = "https://demo.thingsboard.io"

@pytest.fixture(scope="module")
def auth_token():
    """Authenticates and fetches JWT token."""
    login_url = f"{BASE_URL}/api/auth/login"
    payload = {
        "username": "tenant@thingsboard.org",
        "password": "tenant"
    }
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(login_url, json=payload, headers=headers, timeout=10)
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json().get("token")
    assert token is not None, "JWT token missing in response"
    return token

def test_fetch_device_telemetry(auth_token):
    headers = {
        "X-Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    # 1. Fetch Tenant Devices to get a valid deviceId dynamically
    devices_res = requests.get(
        f"{BASE_URL}/api/tenant/devices?pageSize=10&page=0",
        headers=headers,
        timeout=10
    )
    assert devices_res.status_code == 200
    devices_data = devices_res.json().get("data", [])
    assert len(devices_data) > 0, "No devices found in tenant account."
    
    device_id = devices_data[0]["id"]["id"]

    # 2. Query Telemetry with Retry / Polling Logic
    telemetry_url = f"{BASE_URL}/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries"
    
    max_retries = 5
    retry_delay = 3
    telemetry_data = {}
    
    for attempt in range(max_retries):
        response = requests.get(telemetry_url, headers=headers, timeout=10)
        if response.status_code == 200:
            telemetry_data = response.json()
            if len(telemetry_data) > 0:
                break
        time.sleep(retry_delay)
    
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    assert len(telemetry_data) > 0, "Telemetry data stream is empty after retries."

    # 3. Schema & Data Type Validation (3-5 key fields)
    for key, val_list in telemetry_data.items():
        assert isinstance(val_list, list), f"Expected list for key {key}"
        latest_entry = val_list[0]
        assert "ts" in latest_entry, "Timestamp missing in telemetry point"
        assert "value" in latest_entry, "Value missing in telemetry point"
        # Validate timestamp is valid integer epoch milliseconds
        assert isinstance(latest_entry["ts"], int)

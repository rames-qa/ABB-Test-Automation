import os
import re
import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="module")
def ensure_screenshot_dir():
    os.makedirs("screenshots", exist_ok=True)

def test_device_telemetry_dashboard(page: Page, ensure_screenshot_dir):
    # 1. Login
    page.goto("https://demo.thingsboard.io/login")
    page.fill("input[type='email']", "tenant@thingsboard.org")
    page.fill("input[type='password']", "tenant")
    page.click("button[type='submit']")
    
    # Wait for dashboard load / navigation
    page.wait_for_url("**/home", timeout=15000)
    
    # 2. Navigate to Dashboards -> All -> "Device Telemetry Dashboard"
    # Resilient navigation via URL or side menu
    page.goto("https://demo.thingsboard.io/dashboards")
    
    # Click search or filter for "Device Telemetry Dashboard"
    dashboard_card = page.locator("td, mat-cell").filter(has_text="Device Telemetry Dashboard").first
    if dashboard_card.is_visible():
        dashboard_card.click()
    else:
        # Fallback direct search input
        page.fill("input[placeholder*='Search']", "Device Telemetry Dashboard")
        page.locator("mat-row, tr").first.click()

    # Wait for dashboard widgets to load
    page.wait_for_selector("tb-dashboard-widget, .tb-widget", timeout=20000)

    # 3. Validate Widgets & Labels
    for label in ["Temperature", "Humidity", "Power Consumption"]:
        widget = page.locator(f"text={label}")
        expect(widget.first).to_be_visible(timeout=10000)

    # 4. Assert streamed values fall within an acceptable numeric range
    # Select first numeric card value on the dashboard
    value_element = page.locator(".tb-numeric-value, .value, .card-value").first
    if value_element.is_visible():
        val_text = value_element.inner_text().strip()
        numeric_val = float(re.findall(r"[-+]?\d*\.\d+|\d+", val_text)[0])
        assert -50 <= numeric_val <= 200, f"Value {numeric_val} out of bounds!"

    # 5. Capture Screenshot Evidence
    screenshot_path = "screenshots/device_telemetry_dashboard.png"
    page.screenshot(path=screenshot_path, full_page=True)
    assert os.path.exists(screenshot_path), "Screenshot file was not saved successfully."

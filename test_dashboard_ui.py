import os
import re
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "https://demo.thingsboard.io"

USERNAME = os.getenv("TB_USERNAME")
PASSWORD = os.getenv("TB_PASSWORD")


@pytest.fixture(scope="module")
def ensure_screenshot_dir():
    os.makedirs("screenshots", exist_ok=True)


def test_device_telemetry_dashboard(page: Page, ensure_screenshot_dir):

    if not USERNAME or not PASSWORD:
        pytest.fail(
            "Missing credentials. Set TB_USERNAME and TB_PASSWORD environment variables."
        )

    page.goto(
        f"{BASE_URL}/login",
        wait_until="domcontentloaded"
    )

    page.locator("input[type='email']").fill(USERNAME)
    page.locator("input[type='password']").fill(PASSWORD)
    page.locator("button[type='submit']").click()

    page.wait_for_timeout(5000)

    if "/login" in page.url:
        page.screenshot(
            path="screenshots/login_failed.png",
            full_page=True
        )

        pytest.fail(
            f"Login failed. Current URL: {page.url}"
        )

    print("Login successful")

    page.goto(
        f"{BASE_URL}/dashboards",
        wait_until="networkidle"
    )

    dashboard = page.locator(
        "text=Device Telemetry Dashboard"
    ).first

    expect(dashboard).to_be_visible(timeout=15000)
    dashboard.click()

    page.wait_for_selector(
        "tb-dashboard-widget",
        timeout=20000
    )

    for widget in ["Temperature", "Humidity", "Power"]:
        expect(
            page.locator(f"text={widget}").first
        ).to_be_visible(timeout=10000)

    print("Widgets validated")

    values = page.locator(
        ".tb-numeric-value,.value,.card-value"
    )

    if values.count() > 0:
        value_text = values.first.inner_text()

        numbers = re.findall(
            r"[-+]?\d*\.\d+|\d+",
            value_text
        )

        if numbers:
            telemetry_value = float(numbers[0])

            assert -50 <= telemetry_value <= 200, (
                f"Invalid telemetry value: {telemetry_value}"
            )

            print(
                "Telemetry value:",
                telemetry_value
            )

    screenshot_path = (
        "screenshots/device_telemetry_dashboard.png"
    )

    page.screenshot(
        path=screenshot_path,
        full_page=True
    )

    assert os.path.exists(screenshot_path)

    print(
        "Dashboard validation completed successfully"
    )

import argparse
from dataclasses import dataclass
import io
import os
from pathlib import Path
import requests
import subprocess
import zipfile

import polars as pl
from selenium import webdriver
from selenium.common import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


@dataclass
class BillingInformation:
    student: str
    billing_item: str
    element: WebElement


def _transform_to_chromedriver_platform_key(platform: str) -> str:
    match platform:
        case str(platform_str) if "Linux" in platform_str:
            return "linux64"
        case str(platform_str) if "Darwin" in platform_str:
            cpu_version = subprocess.run(
                ["uname", "-m"], capture_output=True, text=True
            ).stdout
            return "mac-x64" if "x86_64" in cpu_version else "mac-arm64"
        case str(platform_str) if "MINGW32_NT" in platform_str:
            return "win32"
        case str(platform_str) if "MINGW64_NT" in platform_str:
            return "win64"
        case _:
            raise AttributeError(f"Platform could not be found or matched: {platform}")


def _download_chromedriver(user_platform: str, chromedriver_path: Path) -> None:
    # Find the current Chrome version
    if "win" in user_platform:
        chrome_version_extraction_command = [
            "wmic",
            "datafile",
            "where",
            'name="C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"',
            "get",
            "Version",
            "/value",
        ]
        raw_version = subprocess.run(
            chrome_version_extraction_command, capture_output=True, text=True
        ).stdout.lower()
        # Check in the non-x86 directory if not present in that one
        if "version" not in raw_version:
            raw_version = subprocess.run(
                list(
                    map(
                        lambda command_part: command_part.replace(" (x86)", ""),
                        chrome_version_extraction_command,
                    )
                ),
                capture_output=True,
                text=True,
            ).stdout.lower()
            if "version" not in raw_version:
                raise RuntimeError(
                    "Chrome is not installed. The program cannot proceed."
                )
        chrome_version = raw_version.split("version=")[1].strip()
    else:
        chrome_version = (
            subprocess.run(
                ["google-chrome", "--version"], capture_output=True, text=True
            )
            .stdout.split()[-1]
            .strip()
        )
    print(f"Detected Chrome version: {chrome_version}")

    # Find the corresponding download URL for the matching chromedriver
    CHROMEDRIVER_VERSIONS_LINK = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
    versions = requests.get(CHROMEDRIVER_VERSIONS_LINK).json()
    chromedriver_platforms = next(
        filter(
            lambda version_info: version_info["version"] == chrome_version,
            versions["versions"],
        )
    )["downloads"]["chromedriver"]
    chromedriver_link = next(
        filter(
            lambda platform_info: platform_info["platform"] == user_platform,
            chromedriver_platforms,
        )
    )["url"]

    # Download chromedriver and make it an executable file if needed
    request = requests.get(chromedriver_link)
    if not request.ok:
        raise RuntimeError("Chromedriver download failed. The program cannot proceed.")
    file = zipfile.ZipFile(io.BytesIO(request.content))
    file.extractall()

    if "win" not in user_platform:
        subprocess.run(["chmod", "+x", chromedriver_path])
    print("Chromedriver downloaded!")


def extract_information_from_tooltip(
    tooltip_element: WebElement,
) -> BillingInformation | None:
    tooltip = tooltip_element.get_attribute("tooltip")
    if tooltip is None:
        return None
    tooltip_parts = tooltip.split("<br />")
    return BillingInformation(
        tooltip_parts[0].strip(),
        tooltip_parts[1].split("-", 1)[0].strip(),
        tooltip_element,
    )


def main(filename: str) -> None:
    """Downloads the corresponding Chromedriver if needed and writes the content of the filename into the Clickedu website.

    PARAMETERS
    ----------
    filename : str
        Path of the file with the values for the billable concepts per student
    """
    # Check whether Chromedriver is available or download it
    print("Checking platform version...")
    try:
        user_platform = _transform_to_chromedriver_platform_key(
            subprocess.run(["uname"], capture_output=True, text=True).stdout
        )
    except Exception:
        raise RuntimeError(
            "User platform could not be matched. Unknown Chromedriver needed. The program cannot proceed."
        )
    print("Checking matching version of Chromedriver...")
    chromedriver_path = (
        Path(f"chromedriver-{user_platform}")
        / f"chromedriver{'.exe' if 'win' in user_platform else ''}"
    ).resolve()
    if not os.path.exists(chromedriver_path):
        print("Downloading the matching chromedriver...")
        try:
            _download_chromedriver(user_platform, chromedriver_path)
        except Exception:
            raise RuntimeError(
                "Chromedriver download failed. The program cannot proceed."
            )

    # Configure Chrome options
    opts = Options()
    opts.add_argument("--start-maximized")

    # Configure ChromeDriver service
    service = Service(str(chromedriver_path))

    # Start the Chrome driver with the configured options and service
    print("Opening browser...")
    try:
        driver = webdriver.Chrome(service=service, options=opts)
        driver.get("https://santjosep.clickedu.eu/user.php?action=login")
    except Exception:
        raise RuntimeError(
            "The current Chromedriver and Chrome versions do not match. Remove the Chromedriver directory and run this script again."
        )

    # Define target strings
    PAGE_TITLE_CLASS = "titol_pagina"
    PAGE_TITLE = "Assignació de conceptes facturables als usuaris"
    TABLE_ID = "unique_id"

    # Wait until the driver is in the correct page
    errors = [NoSuchElementException, ElementNotInteractableException]
    wait = WebDriverWait(
        driver, timeout=60, poll_frequency=2, ignored_exceptions=errors
    )
    print(
        "Please input the login credentials in the opened browser and navigate to the billing page with the necessary students and billable concepts within one minute"
    )
    try:
        wait.until(
            lambda _: len(driver.find_elements(By.CLASS_NAME, PAGE_TITLE_CLASS)) == 1
            and driver.find_elements(By.CLASS_NAME, PAGE_TITLE_CLASS)[0].text
            == PAGE_TITLE
            and len(driver.find_elements(By.ID, TABLE_ID)) == 1
        )
    except Exception:
        raise RuntimeError(
            "The page did not contain the expected elements on time. Try again"
        )

    # Read the imported data
    data = pl.read_csv(filename, separator=";")

    # Find the relevant elements to add the values for the billable concepts
    table = driver.find_element(By.ID, "unique_id")
    # Needing to ignore the types in filters related to this variable since it considers it as list[BillingInformation | None] when it cannot be None due to the filter
    billing_fields = list(
        filter(
            lambda result: result is not None,
            map(
                extract_information_from_tooltip,
                table.find_elements(By.TAG_NAME, "div"),
            ),
        )
    )

    NAME_COLUMN = "Usuari"
    clean_data = data[
        :,
        # type: ignore
        [
            any(
                map(
                    lambda field: col == NAME_COLUMN or field.billing_item == col,  # type: ignore
                    billing_fields,
                )
            )
            for col in data.columns
        ],
    ]
    print(
        f"No s'han trobat els següents conceptes: {[col for col in data.columns if col not in clean_data.columns]}"
    )

    # Add each value to the correct cell and warn if any cannot be added
    for billing_info in clean_data.iter_rows(named=True):
        student_fields: list[BillingInformation] = list(
            filter(
                lambda field: field.student == billing_info[NAME_COLUMN],  # type: ignore
                billing_fields,
            )
        )
        if len(student_fields) == 0:
            print(f"No s'ha trobat l'alumne {billing_info[NAME_COLUMN]}")
            continue
        items = (
            item
            for item in billing_info
            if item != NAME_COLUMN and billing_info[item] is not None
        )
        for item in items:
            try:
                input_ancestor_information = next(
                    filter(lambda field: field.billing_item == item, student_fields)
                )
            except StopIteration:
                print(
                    f"No s'ha trobat el concepte {item} per l'alumne {billing_info[NAME_COLUMN]}"
                )
                continue
            checkbox = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    next(
                        filter(
                            lambda input: input.get_attribute("type") == "checkbox",
                            input_ancestor_information.element.find_elements(
                                By.TAG_NAME, "input"
                            ),
                        )
                    )
                )
            )
            # Activate the input if it is not available yet (text input for desired value is not available otherwise)
            if not checkbox.is_selected():
                ActionChains(driver).move_to_element(checkbox).pause(
                    1
                ).click().perform()
            input = next(
                filter(
                    lambda input: input.get_attribute("type") == "text",
                    input_ancestor_information.element.find_elements(
                        By.TAG_NAME, "input"
                    ),
                )
            )
            input.clear()  # Needed if there is a previous value
            input.send_keys(billing_info[item])

    # Wait until the user saves or 15 minutes have passed
    MAX_WAITING_TIME_IN_SECONDS = 15 * 60
    WebDriverWait(driver, MAX_WAITING_TIME_IN_SECONDS).until(
        EC.invisibility_of_element((By.ID, TABLE_ID))
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Importació",
        description="Importa valors assignats als conceptes facturables de CSV a ClickEdu",
    )
    parser.add_argument("filename", help="Drag and drop the CSV to be imported")
    args = parser.parse_args()
    main(args.filename)

#!/usr/bin/env -S uv run
"""
Import script for billable concepts per student.

This script sets the values of the billable concepts per student defined in a CSV into Clickedu. The user needs to log in manually and navigate to the corresponding page for security and flexibility.

The script can be run from the command line with the arguments:
    uv run scripts/importació/importació.py FILENAME

The user should double-check and save afterwards. It also prints if it was not possible to add a student or a billable concept.
"""

# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "polars>=1.31.0",
#     "scripts",
#     "selenium>=4.34.2",
#     "webdriver_manager>=4.0.2",
# ]
# ///

import argparse
from dataclasses import dataclass

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
from webdriver_manager.chrome import ChromeDriverManager


@dataclass
class BillingInformation:
    student: str
    billing_item: str
    element: WebElement


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
    # Configure Chrome options
    opts = Options()
    opts.add_argument("--start-maximized")

    # Start the Chrome driver with the configured options and service
    print("Opening browser...")
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=opts
        )
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
        description="Importa valors assignats als conceptes facturables de CSV a Clickedu",
    )
    parser.add_argument("filename", help="Drag and drop the CSV to be imported")
    args = parser.parse_args()
    main(args.filename)

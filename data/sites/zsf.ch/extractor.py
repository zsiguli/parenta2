from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from data.scraped_camp import ScrapedCamp
from typing import List, Optional
from typing_extensions import Literal


def parse_age_range(class_range: str) -> Optional[str]:
    try:
        class_from, class_to = map(int, class_range.split(" - "))
        age_from = class_from + 6
        age_to = class_to + 6
        return f"{age_from} - {age_to}"
    except:
        return None


def parse_date_range(date_text: str) -> str:
    # Assuming the format is 'DD.MM. – DD.MM.YYYY' or 'DD.MM.YYYY – DD.MM.YYYY'
    try:
        parts = date_text.replace(" – ", ".").split(".")
        if len(parts) == 6:
            start_date = f"{parts[2]}-{parts[1]:02}-{parts[0]:02}"
            end_date = f"{parts[5]}-{parts[4]:02}-{parts[3]:02}"
        elif len(parts) == 4:
            start_date = f"2025-{parts[1]:02}-{parts[0]:02}"
            end_date = f"2025-{parts[3]:02}-{parts[2]:02}"
        else:
            return date_text
        return f"{start_date} to {end_date}"
    except:
        return date_text


def parse_price_range(price_text: str) -> Optional[str]:
    try:
        return price_text.split(": ")[1].split(",")[0]
    except:
        return None


def extract_camps(driver: webdriver.Chrome, url: str) -> List[ScrapedCamp]:
    driver.get(url)
    camps = []

    try:
        registration_deadline = driver.find_element(By.CSS_SELECTOR, ".ym-grid .boxx p strong").text.split(",")[1].strip()
    except NoSuchElementException:
        registration_deadline = None

    camp_elements = driver.find_elements(By.CSS_SELECTOR, ".fp-camp")

    for camp_element in camp_elements:
        try:
            title = camp_element.find_element(By.TAG_NAME, "h3").text
            description = camp_element.find_element(By.TAG_NAME, "p").text
            location = camp_element.find_element(By.CLASS_NAME, "fp-campbox-location").text
            date_range = camp_element.find_element(By.CLASS_NAME, "fp-campbox-date").text.split("\n")[0]
            age_range = camp_element.find_element(By.CLASS_NAME, "fp-campbox-date").text.split("\n")[1].replace("Klassen ", "")
            price_range = camp_element.find_element(By.CSS_SELECTOR, "p strong").text
            availability_url = camp_element.find_element(By.CSS_SELECTOR, ".fp-online a").get_attribute("href")

            camp = ScrapedCamp(
                title=title,
                description=description,
                images=[],
                location=location,
                date_range=parse_date_range(date_range),
                daily_format="overnight",
                age_range=parse_age_range(age_range),
                gender_restriction=None,
                price_range=parse_price_range(price_range),
                registration_deadline=registration_deadline,
                contact_phone="044 311 55 56",
                contact_email="anmeldung@zsf.ch",
                availability_url=availability_url,
                availability_css_selector=".msg-full"
            )
            camps.append(camp)
            
        except NoSuchElementException:
            continue

    return camps
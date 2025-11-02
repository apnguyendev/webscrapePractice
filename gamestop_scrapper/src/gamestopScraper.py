# Import third party libraries
import re
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE = "https://www.gamestop.com"

def _to_price(text):
    if not text:
        return None
    m = re.search(r"(\d+(?:\.\d{1,2})?)", text.replace(",", ""))
    return float(m.group(1)) if m else None

def _serial_from_href(href):
    if not href:
        return None
    m = re.search(r"/PSA(\d+)\.html", href)
    return m.group(1) if m else None

def get_card_info():
    url = (
        "https://www.gamestop.com/graded-trading-cards"
        "?q=&offset=0"
        "&refine=cgid=gradedcollectibles"
        "&refine=price=(0..10000)"
        "&refine=c_category=TCG+Cards"
        "&limit=25&sort=release-date-descending"
    )
    """
    Opens Chrome, navigates to the graded trading cards page,
    and returns a list of dicts with product fields.
    """
    service = Service(executable_path="chromedriver.exe")
    driver = webdriver.Chrome(service=service)

    rows = []
    try:
        driver.get(url)

        # Wait until the product grid loads
        cardContainer = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".item-grid.items-center"))
        )

        # Get all anchor tags inside the grid
        cards = cardContainer.find_elements(By.CSS_SELECTOR, "a.router-card-link")

        for card in cards:
            # URL + PSA serial
            href = card.get_attribute("href")
            full_url = urljoin(BASE, href) if href else None
            psa_serial = _serial_from_href(href)

            # Name (prefer IMG alt, then description, fallback to visible name)
            name = None
            try:
                img = card.find_element(By.CSS_SELECTOR, "img.product-image")
                name = img.get_attribute("alt") or img.get_attribute("description")
            except Exception:
                pass
            if not name:
                try:
                    name = card.find_element(
                        By.CSS_SELECTOR, ".product-card-name .main-text"
                    ).text.strip()
                except Exception:
                    name = None

            # Prices
            regular_price_text = None
            pro_price_text = None
            try:
                regular_price_text = card.find_element(
                    By.CSS_SELECTOR, "p.price-text.regular-price"
                ).text.strip()
            except Exception:
                pass
            try:
                pro_price_text = card.find_element(
                    By.CSS_SELECTOR, "span.pro-price"
                ).text.strip()
            except Exception:
                pass

            row = {
                "url": full_url,
                "name": name,
                "regular_price": _to_price(regular_price_text),
                "pro_price": _to_price(pro_price_text),
                "psa_serial": psa_serial,
            }
            rows.append(row)

    except Exception as e:
        print(f"[Error] Failed to scrape cards: {e}")

    finally:
        driver.quit()

    return rows

# Grab all card urls. Will need to extract the following data from each URL : Pokemon card name, psa grade, serial #
def get_card_urls():
    url = (
        "https://www.gamestop.com/graded-trading-cards"
        "?q=&offset=0"
        "&refine=cgid=gradedcollectibles"
        "&refine=price=(0..10000)"
        "&refine=c_category=TCG+Cards"
        "&limit=25&sort=release-date-descending"
    )
    """
    Opens Chrome, navigates to the given GameStop graded trading cards page,
    and returns a list of all card URLs from the product grid.
    Automatically handles driver setup, waiting, and cleanup.
    """
    service = Service(executable_path="chromedriver.exe")
    driver = webdriver.Chrome(service=service)

    urls = []
    try:
        driver.get(url)

        # Wait until the product grid loads
        cardContainer = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".item-grid.items-center"))
        )

        # Get all anchor tags inside the grid
        cards = cardContainer.find_elements(By.CSS_SELECTOR, "a.router-card-link")

        for card in cards:
            href = card.get_attribute("href")
            if href:
                urls.append(urljoin(BASE, href))

    except Exception as e:
        print(f"[Error] Failed to grab card URLs: {e}")

    finally:
        driver.quit()

    return urls

# Parser: Extract card details from URL - legacy
def parse_card_url(url):
    """
    Extracts year, card name, PSA grade, and PSA serial number from a GameStop card URL.
    """
    path = urlparse(url).path  # Extract path part of the URL
    pattern = re.compile(
        r"/(?P<year>\d{4})-(?P<card>.+?)-psa-(?P<grade>\d+)/PSA(?P<serial>\d+)\.html"
    )

    match = pattern.search(path)
    if not match:
        return None

    year = match.group("year")
    card_name = match.group("card").replace("-", " ").strip()
    psa_grade = match.group("grade")
    serial_number = match.group("serial")

    return {
        "year": year,
        "card_name": card_name,
        "psa_grade": psa_grade,
        "serial_number": serial_number,
    }

if __name__ == "__main__":

    card_urls = get_card_info()


# Import third party libraries
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE = "https://www.gamestop.com"

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


if __name__ == "__main__":

    card_urls = get_card_urls()

    print(f"Found {len(card_urls)} cards:\n")
    for u in card_urls:
        print(u)

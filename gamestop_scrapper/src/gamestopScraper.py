# Import third party libraries
import re
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException

import json
import os
from datetime import datetime, timedelta

import time
from selenium.webdriver.common.keys import Keys

GAMESTOP_HOME = "https://www.gamestop.com"
ALT_HOME = "https://app.alt.xyz/"

STATE_FILE = "cards_state.json"


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
            full_url = urljoin(GAMESTOP_HOME, href) if href else None
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

            # PSA grade (from the badge element or the end of name)
            psa_grade = None
            try:
                badge = card.find_element(
                    By.CSS_SELECTOR, ".grade-badge-container .q-badge"
                )
                psa_grade = badge.text.strip()
            except Exception:
                # fallback if PSA appears in name
                if name:
                    m = re.search(r"(PSA\s*\d+)", name)
                    psa_grade = m.group(1) if m else None

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
                "psa_grade": psa_grade,
            }
            rows.append(row)

    except Exception as e:
        print(f"[Error] Failed to scrape cards: {e}")

    finally:
        driver.quit()

    return rows


# =========================
# JSON state helpers
# =========================

def load_state(filename=STATE_FILE):
    """
    Load existing card state JSON, or return an empty dict if none.
    Internally we use a dict keyed by psa_serial for easy lookup.
    """
    if not os.path.exists(filename):
        return {}

    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[WARN] Could not load state file '{filename}': {e}")
        return {}

    state = {}
    for card in data:
        serial = card.get("psa_serial")
        if serial:
            state[serial] = card
    return state


def save_state(state, filename=STATE_FILE):
    """
    Save state dict (keyed by psa_serial) as a JSON list.
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(list(state.values()), f, indent=4)
        print(f"[OK] Saved state with {len(state)} cards → {filename}")
    except Exception as e:
        print(f"[ERROR] Could not save state file '{filename}': {e}")


def needs_processing(card, existing_entry, price_change_threshold=0.01, max_age_hours=24):
    """
    Decide if this card should be sent to ALT (in the future).
    - If new (no existing entry) → True
    - If GameStop price changed by >= threshold → True
    - If last_checked older than max_age_hours → True
    - Else → False
    """
    # Brand new serial: always process
    if existing_entry is None:
        return True

    current_price = card.get("regular_price")
    old_price = existing_entry.get("last_gs_price")

    # 1) Price changed enough?
    if current_price is not None and old_price is not None:
        if old_price == 0 and current_price != 0:
            return True

        denominator = old_price if old_price != 0 else 0.01
        change_ratio = abs(current_price - old_price) / abs(denominator)

        if change_ratio >= price_change_threshold:
            return True

    # 2) Too old? (force refresh after some time)
    last_checked_str = existing_entry.get("last_checked")
    if last_checked_str:
        try:
            last_checked = datetime.fromisoformat(last_checked_str)
            if datetime.utcnow() - last_checked > timedelta(hours=max_age_hours):
                return True
        except Exception:
            return True  # be safe if parsing fails

    return False


# =========================
# ALT interaction (step 1)
# =========================

def search_alt_for_serial(serial):
    """
    Open ALT, search for ONE PSA cert #, hit Enter,
    then click the first result row button (the one that
    contains the card title text, e.g.,
    '2025 Pokemon Scarlet and Violet Journey Together Illustration Rare Wailord #162').
    """
    if not serial:
        print("[INFO] No serial provided for ALT.")
        return

    service = Service(executable_path="chromedriver.exe")
    driver = webdriver.Chrome(service=service)

    try:
        driver.get(ALT_HOME)

        # Wait for the search input to be present
        search_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.ID, "universal-search-autocomplete")
            )
        )

        # Type serial and press ENTER
        search_input.clear()
        search_input.send_keys(serial)
        search_input.send_keys(Keys.ENTER)
        print(f"[ALT] Submitted serial {serial}")

        # Give React a moment to start rendering results
        time.sleep(1)

        skip_labels = {"Filters", "Listed Date", "Sold listings", "Save search"}

        def click_result_button():
            """
            Keep trying to find and click a 'real' result row button.
            Returns True if clicked, False if time runs out.
            """
            end_time = time.time() + 20  # up to 20 seconds total
            while time.time() < end_time:
                try:
                    buttons = driver.find_elements(
                        By.XPATH,
                        "//main//button[contains(@class, 'MuiButtonBase-root')]"
                    )
                except StaleElementReferenceException:
                    # DOM changed while getting buttons; retry
                    time.sleep(0.5)
                    continue

                for btn in buttons:
                    try:
                        text = btn.text.strip()
                    except StaleElementReferenceException:
                        # This button went stale; skip and keep scanning
                        continue

                    if not text:
                        continue
                    if text in skip_labels:
                        continue
                    # Listing titles are long text, not tiny labels
                    if len(text) <= 20:
                        continue

                    # Try clicking this candidate immediately
                    try:
                        btn.click()
                        print(f"[ALT] Clicked result button with text: {text[:80]}...")
                        return True
                    except StaleElementReferenceException:
                        # It went stale between reading text and click; try again
                        break  # break inner loop, re-scan buttons

                time.sleep(0.5)

            return False

        clicked = click_result_button()
        if not clicked:
            print("[ALT] Could not find a suitable result button to click within timeout.")

        # Short pause so you can visually confirm while testing
        time.sleep(3)

    except Exception as e:
        print(f"[ERROR] Problem interacting with ALT: {e}")

    finally:
        driver.quit()


if __name__ == "__main__":

    # 1) Gamestop data is extracted here
    cardsList = get_card_info()

    # 2) Load JSON state from previous runs (if any)
    state = load_state()

    # 3) Figure out which cards NEED processing (for ALT)
    to_process = []
    for card in cardsList:
        serial = card.get("psa_serial")
        if not serial:
            continue

        existing = state.get(serial)
        if needs_processing(card, existing):
            to_process.append(card)

    print(f"[INFO] Cards that would be sent to ALT: {len(to_process)}")

    # Extract just the serials for the ALT step
    serials_for_alt = [c["psa_serial"] for c in to_process if c.get("psa_serial")]

    # 4) Send serials to ALT search (no scraping yet, just type + ENTER)
    #    You can comment this out while debugging.
    if serials_for_alt:
        first_serial = serials_for_alt[0]
        print(f"[INFO] Testing ALT search with serial: {first_serial}")
        search_alt_for_serial(first_serial)

    # 5) Update state with latest GameStop info
    for card in cardsList:
        serial = card.get("psa_serial")
        if not serial:
            continue

        existing = state.get(serial)
        if existing is None:
            existing = {
                "psa_serial": serial,
            }
            state[serial] = existing

        existing["name"] = card.get("name")
        existing["url"] = card.get("url")
        existing["last_gs_price"] = card.get("regular_price")
        existing["last_gs_pro_price"] = card.get("pro_price")
        existing["psa_grade"] = card.get("psa_grade")
        # last_checked / last_alt_price will be filled in later

    # 6) Save updated state back to JSON
    save_state(state)

import requests, itertools
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
from lxml import html

targetUrl = "https://www.gamestop.com/api/proxy/search/shopper-search/v1/organizations/f_ecom_bcpk_prd/product-search"


# Note : chatgpt generated params, no clue if this is actually valid. Will revisit this later
params = {
    "siteId": "gamestop-us",
    "q": "",
    "refine": ["cgid=gradedcollectibles", "price=(0..10000)", "c_category=TCG Cards"],
    "sort": "release-date-descending",
    "expand": "custom_properties,images,prices",
    "offset": 0,
    "limit": 25
}

headers = {"User-Agent": "Mozilla/5.0"}

r = requests.get(targetUrl, params=params, headers=headers)
print(r.status_code)
print(r.headers.get("Content-Type"))
print(r.text[:500])

# data = r.json()

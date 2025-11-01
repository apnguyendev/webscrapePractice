import requests
from urllib.parse import urljoin
from lxml import html

# Target URL
TARGETURL = (
    "https://www.gamestop.com/graded-trading-cards?q=&offset=0&refine=cgid=gradedcollectibles&refine=price=(0..10000)&refine=c_category=TCG+Cards&limit=25&sort=release-date-descending"
)


LISTING = (
    "https://www.gamestop.com/graded-collectibles/"
    "graded-cards/search?cgid=gradedcollectibles"
)

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/141.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.gamestop.com",
    "Referer": LISTING,
}

r = requests.get(TARGETURL, headers=headers)


print("Status:", r.status_code)
print("Content-Type:", r.headers.get("Content-Type"))
# print(r.text)


# data = r.json()
# print(data)

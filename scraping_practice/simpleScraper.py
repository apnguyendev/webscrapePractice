import requests
from lxml import html

URL = "https://quotes.toscrape.com/"
headers = {"User-Agent": "Mozilla/5.0 (compatible; my-scraper/0.1)"}

r = requests.get(URL, headers=headers, timeout=15)
r.raise_for_status()

tree = html.fromstring(r.content)
tree.make_links_absolute(URL)  # convert relative links to absolute

# Each quote lives in <div class="quote">
for q in tree.xpath('//div[contains(@class,"quote")]'):
    text  = q.xpath('normalize-space(.//span[@class="text"])')
    author = q.xpath('normalize-space(.//small[@class="author"])')
    tags   = q.xpath('.//div[@class="tags"]/a[@class="tag"]/text()')
    print({"text": text, "author": author, "tags": tags})
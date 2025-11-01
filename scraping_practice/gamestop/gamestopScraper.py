from lxml import html
from scrapfly import ScrapflyClient, ScrapeConfig, ScrapeApiResponse
from urllib.parse import urljoin

BASE = "https://www.gamestop.com"

# Initialize Scrapfly
scrapfly= ScrapflyClient(key="scp-live-8bce1cd02b76464ba1a709eca710a4fc")

# Scrape target gamestop page, for all parameters review : https://scrapfly.io/docs/scrape-api/getting-started#spec
response: ScrapeApiResponse = scrapfly.scrape(ScrapeConfig(
   url="https://www.gamestop.com/graded-trading-cards?q=&offset=0&refine=cgid=gradedcollectibles&refine=price=(0..10000)&refine=c_category=TCG+Cards&limit=25&sort=release-date-descending",
   proxy_pool="public_residential_pool",
   country="us",
   asp=True,
   render_js=True,
))

rawHtml = response.scrape_result["content"]

htmlTree = html.fromstring(rawHtml)

card_list = htmlTree.xpath('//div[contains(@class, "item-grid items-center")]')

results = []

for card in card_list:
    cardhref = card.xpath('.//a[contains(@href,"/graded-trading-cards/graded-cards")]/@href')
    results.append({"url": cardhref})
    
# for r in results:
#     print(r)

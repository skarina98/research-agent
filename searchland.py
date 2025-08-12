# searchland.py
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

BASE_URL = "https://searchland.co.uk"

async def lookup_property(address, postcode, auction_date):
    """
    Look up a property in Searchland by address & postcode.
    Extract owner, sold_price, sold_date.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state="sessions/searchland.json")
        page = await context.new_page()

        await page.goto(BASE_URL)
        await page.fill("#search-input", f"{address} {postcode}")
        await page.press("#search-input", "Enter")
        await page.wait_for_selector(".property-result")

        owner = sold_price = sold_date = None

        try:
            owner = await page.locator(".owner-name").text_content()
        except:
            pass

        try:
            sold_price = await page.locator(".sold-price").text_content()
            sold_date_str = await page.locator(".sold-date").text_content()
            sold_date = datetime.strptime(sold_date_str, "%d %b %Y").strftime("%Y-%m-%d")
        except:
            pass

        await browser.close()
    return {
        "owner": owner,
        "sold_price": sold_price,
        "sold_date": sold_date
    }

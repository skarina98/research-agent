from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context("./sessions/eig", headless=False)
        page = browser.new_page()
        page.goto("https://example.com")  # EIG login
        input("Log in to EIG and press Enter...")
        browser.close()

        browser = p.chromium.launch_persistent_context("./sessions/searchland", headless=False)
        page = browser.new_page()
        page.goto("https://example.com")  # Searchland login
        input("Log in to Searchland and press Enter...")
        browser.close()

if __name__ == "__main__":
    main()

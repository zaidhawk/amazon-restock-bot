import os
import sys
from playwright.sync_api import sync_playwright, BrowserContext, Page

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/133.0.0.0 Safari/537.36"
)

def get_browser_context(user_data_dir: str = "./amazon_profile", headless: bool = False, block_assets: bool = False):
    """
    Launches a persistent Chromium browser context so your Amazon login session,
    cookies, 1-click settings, and cart state are preserved between runs.
    Optionally blocks heavy media/images to accelerate reload speeds.
    """
    abs_profile = os.path.abspath(user_data_dir)
    os.makedirs(abs_profile, exist_ok=True)

    playwright = sync_playwright().start()

    args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars",
        "--start-maximized",
        "--lang=en-CA,en-US,en",
    ]

    context: BrowserContext = playwright.chromium.launch_persistent_context(
        user_data_dir=abs_profile,
        headless=headless,
        viewport=None,
        args=args,
        user_agent=DEFAULT_USER_AGENT,
        locale="en-CA",
        timezone_id="America/Toronto",
        accept_downloads=False,
    )

    # Invalidate navigator.webdriver flag
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)

    # Accelerated monitoring: block high-bandwidth images/media
    if block_assets:
        def intercept_route(route):
            if route.request.resource_type in ["image", "media", "font"]:
                route.abort()
            else:
                route.continue_()
        context.route("**/*", intercept_route)

    return playwright, context

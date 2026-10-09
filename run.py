import argparse
import json
import random
import time
from datetime import datetime

from browser import get_browser_context
from buyer import Buyer
from monitor import StockMonitor
from notifier import Notifier


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-checks", type=int, help="stop after N checks (for testing)")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()

    with open("config.json", encoding="utf-8-sig") as f:
        config = json.load(f)

    url = config["product_url"]
    title = config.get("product_title", "Amazon product")
    min_wait = config.get("check_interval_seconds_min", 4)
    max_wait = config.get("check_interval_seconds_max", 7)
    profile = config.get("user_data_dir", "./amazon_profile")
    headless = args.headless or config.get("headless", False)

    notifier = Notifier(sound_duration=config.get("sound_alert_duration_seconds", 30))
    monitor = StockMonitor(config, notifier)
    buyer = Buyer(notifier, auto_click_buy_now=config.get("auto_click_buy_now", True))

    print(f"Monitoring: {title}")
    print(f"URL: {url}")
    print(f"Max price: ${config.get('max_price_cad', 'N/A')} | Interval: {min_wait}-{max_wait}s\n")

    playwright, context = get_browser_context(user_data_dir=profile, headless=headless,
                                              block_assets=config.get("block_heavy_images", True))
    page = context.pages[0] if context.pages else context.new_page()

    try:
        page.goto(url, wait_until="commit", timeout=20000)
    except Exception as e:
        log(f"Initial load failed, will retry: {e}")

    checks = 0
    try:
        while True:
            checks += 1
            status = monitor.check_stock(page)

            if status["captcha"]:
                log("CAPTCHA detected - solve it in the browser window.")
                notifier.send_desktop_notification("Amazon CAPTCHA", "Solve the CAPTCHA in the browser window.")
                while monitor.is_captcha_present(page):
                    time.sleep(3)
                log("CAPTCHA solved, resuming.")
                continue

            if status["in_stock"]:
                log(f"IN STOCK! Price: {status['price_str']}")
                if buyer.attempt_checkout(page, title, status["price_str"]):
                    log("Order placed. Exiting.")
                    break
                input("Checkout did not finish - check the browser. Press Enter to resume monitoring...")
                continue

            if args.max_checks and checks >= args.max_checks:
                log(f"Check #{checks}: {status['reason']}. Reached max checks, exiting.")
                break

            delay = round(random.uniform(min_wait, max_wait), 1)
            log(f"Check #{checks}: {status['reason']}. Next check in {delay}s")
            time.sleep(delay)

            try:
                page.reload(wait_until="commit", timeout=12000)
            except Exception as e:
                log(f"Reload failed: {e}")

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        context.close()
        playwright.stop()


if __name__ == "__main__":
    main()

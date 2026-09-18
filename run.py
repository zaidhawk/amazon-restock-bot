import sys
import os
import json
import time
import random
import argparse
from datetime import datetime

from browser import get_browser_context
from notifier import Notifier
from monitor import StockMonitor
from buyer import Buyer

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def load_config(path="config.json") -> dict:
    if not os.path.exists(path):
        print(f"Error: {path} not found!")
        sys.exit(1)
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="Amazon.ca Stock Monitor & Rapid Checkout Bot")
    parser.add_argument("--max-checks", type=int, default=None, help="Stop after N checks (for testing)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    args = parser.parse_args()

    config = load_config()
    product_url = config.get("product_url")
    product_title = config.get("product_title", "Nintendo Switch 2 - Zelda 40th Anniversary")
    min_interval = config.get("check_interval_seconds_min", 4)
    max_interval = config.get("check_interval_seconds_max", 7)
    user_data_dir = config.get("user_data_dir", "./amazon_profile")
    headless = args.headless or config.get("headless", False)
    auto_click = config.get("auto_click_buy_now", True)
    sound_duration = config.get("sound_alert_duration_seconds", 30)
    block_assets = config.get("block_heavy_images", True)

    print("=" * 65)
    print("  AMAZON.CA STOCK MONITOR & RAPID CHECKOUT BOT")
    print("=" * 65)
    print(f"Target URL:    {product_url}")
    print(f"Item:          {product_title}")
    print(f"Max Price:     CAD ${config.get('max_price_cad', 'N/A')}")
    print(f"Interval:      {min_interval}s - {max_interval}s (Jittered)")
    print(f"Asset Boost:   {'Enabled (Fast DOM Reloads)' if block_assets else 'Disabled'}")
    print(f"Mode:          Semi-Automated Checkout (Auto-cart + Confirmation Alert)")
    print(f"Browser:       {'Headless' if headless else 'Visible (Recommended)'}")
    print(f"Profile Dir:   {user_data_dir}")
    if args.max_checks:
        print(f"Test Run:      Will exit after {args.max_checks} check(s)")
    print("=" * 65)

    if not os.path.exists(user_data_dir):
        print("\n[NOTE] No saved login session detected in", user_data_dir)
        print("       Tip: Run 'python login.py' first if you wish to pre-authenticate")
        print("       your Amazon account with 1-Click and Prime shipping.\n")

    notifier = Notifier(sound_duration=sound_duration)
    monitor = StockMonitor(config, notifier)
    buyer = Buyer(notifier, auto_click_buy_now=auto_click)

    print("[1/2] Launching browser session...")
    playwright, context = get_browser_context(user_data_dir=user_data_dir, headless=headless, block_assets=block_assets)
    page = context.pages[0] if context.pages else context.new_page()

    print("[2/2] Connecting to target product page...")
    try:
        page.goto(product_url, wait_until="domcontentloaded", timeout=45000)
    except Exception as e:
        print(f"[Warning] Initial load timeout or error: {e}. Retrying in loop...")

    print("\n>>> Monitoring started! Press Ctrl+C to stop.\n")

    check_count = 0
    try:
        while True:
            check_count += 1
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Check stock
            status = monitor.check_stock(page)

            if status["captcha"]:
                print(f"[{now_str}] [!] CAPTCHA CHALLENGE DETECTED! Alerting user...")
                notifier.send_desktop_notification(
                    "Amazon CAPTCHA Challenge",
                    "Please solve the Amazon CAPTCHA in the open browser window!"
                )
                # Wait until user solves captcha
                while monitor.is_captcha_present(page):
                    time.sleep(3)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] CAPTCHA resolved! Resuming monitor...")
                continue

            if status["in_stock"]:
                print(f"[{now_str}] [***] IN STOCK DETECTED! Price: {status['price_str']}")
                buyer.attempt_checkout(page, product_title, status["price_str"])

                print("\n[Halt] Monitor paused after carting item. Order is ready in your browser.")
                print("Press Enter in this terminal whenever you want to resume monitoring...")
                input()
                print("Resuming monitor...")

            else:
                reason = status.get("reason", "Out of stock")
                if args.max_checks and check_count >= args.max_checks:
                    print(f"[{now_str}] Check #{check_count}: {reason}.")
                    print(f"\n[Test Complete] Reached max-checks limit ({args.max_checks}). Exiting.")
                    break

                delay = round(random.uniform(min_interval, max_interval), 1)
                print(f"[{now_str}] Check #{check_count}: {reason}. Next check in {delay}s...")
                time.sleep(delay)

                try:
                    page.reload(wait_until="domcontentloaded", timeout=30000)
                except Exception as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Reload notice: {e}")

    except KeyboardInterrupt:
        print("\n\nStopping monitor... Exiting safely.")
    finally:
        context.close()
        playwright.stop()
        print("Browser session closed.")

if __name__ == "__main__":
    main()

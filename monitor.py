import sys
import re
from playwright.sync_api import Page

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

class StockMonitor:
    def __init__(self, config: dict, notifier):
        self.config = config
        self.notifier = notifier
        self.product_url = config.get("product_url")
        self.max_price = float(config.get("max_price_cad", 9999.0))
        self.only_amazon = bool(config.get("only_ships_from_amazon", True))

    def is_captcha_present(self, page: Page) -> bool:
        captcha = page.query_selector('form[action*="validateCaptcha"], input#captchacharacters')
        if captcha:
            return True
        body_text = page.content().lower()
        if "enter the characters you see below" in body_text or "type the characters you see in this image" in body_text:
            return True
        return False

    def parse_price(self, price_text: str) -> float:
        if not price_text:
            return 0.0
        cleaned = re.sub(r"[^\d.]", "", price_text)
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def check_stock(self, page: Page) -> dict:
        result = {
            "in_stock": False,
            "captcha": False,
            "price_val": None,
            "price_str": "N/A",
            "seller_info": "Unknown",
            "reason": ""
        }

        # 1. Check CAPTCHA
        if self.is_captcha_present(page):
            result["captcha"] = True
            result["reason"] = "CAPTCHA detected"
            return result

        # 2. Check Availability text
        avail_el = page.query_selector('#availability')
        avail_text = avail_el.inner_text().strip().lower() if avail_el else ""

        # 3. Check purchase buttons
        buy_now = page.query_selector('#buy-now-button, input#buy-now-button')
        add_to_cart = page.query_selector('#add-to-cart-button, input#add-to-cart-button, #preOrderButton')

        has_active_button = False
        if buy_now and buy_now.is_visible() and buy_now.is_enabled():
            has_active_button = True
        if add_to_cart and add_to_cart.is_visible() and add_to_cart.is_enabled():
            has_active_button = True

        # Determine stock presence
        if "currently unavailable" in avail_text or "we don't know when or if this item will be back in stock" in avail_text:
            result["in_stock"] = False
            result["reason"] = "Currently unavailable"
            return result

        if not has_active_button and not ("in stock" in avail_text or "pre-order" in avail_text or "available to ship" in avail_text):
            result["in_stock"] = False
            result["reason"] = "No active checkout buttons found"
            return result

        # If we reached here, item has stock indications
        result["in_stock"] = True

        # 4. Extract Price
        price_el = page.query_selector(
            '#corePriceDisplay_desktop_feature_div .a-offscreen, '
            '#corePrice_desktop .a-offscreen, '
            '#price_inside_buybox, '
            '.priceToPay .a-offscreen'
        )
        if price_el:
            price_str = price_el.inner_text().strip()
            result["price_str"] = price_str
            result["price_val"] = self.parse_price(price_str)

        # 5. Extract Seller / Merchant info
        merchant_el = page.query_selector('#merchant-info, #tabular-buybox')
        if merchant_el:
            result["seller_info"] = merchant_el.inner_text().strip().replace("\n", " | ")

        # 6. Safety check: Max Price
        if result["price_val"] and result["price_val"] > self.max_price:
            print(f"[Safety Filter] Detected price (${result['price_val']:.2f}) exceeds max CAD ${self.max_price:.2f}! Probable scalper.")
            result["in_stock"] = False
            result["reason"] = f"Price ${result['price_val']:.2f} exceeds limit ${self.max_price:.2f}"
            return result

        # 7. Safety check: Ships from Amazon
        if self.only_amazon and result["seller_info"] != "Unknown":
            seller_lower = result["seller_info"].lower()
            if "amazon" not in seller_lower:
                print(f"[Safety Filter] Seller is not Amazon ({result['seller_info']}). Skipping to avoid scalper.")
                result["in_stock"] = False
                result["reason"] = "Third-party seller (only_ships_from_amazon is enabled)"
                return result

        return result

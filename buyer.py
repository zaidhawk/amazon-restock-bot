import time
from playwright.sync_api import Page

BUY_BUTTONS = [
    '#buy-now-button',
    '#preOrderButton',
    'input[name="submit.buy-now"]',
    '#one-click-button',
]
ADD_TO_CART = '#add-to-cart-button'
PROCEED_TO_CHECKOUT = [
    '#attach-sidesheet-checkout-button',
    'input[name="proceedToRetailCheckout"]',
    '#hlb-ptc-btn-native',
    'a[href*="proceedToCheckout"]',
]
PLACE_ORDER = [
    '#submitOrderButtonId input[type="submit"]',
    'input[name="placeYourOrder1"]',
    '#bottomSubmitOrderButtonId input[type="submit"]',
    'input[value*="Place your order" i]',
]
# Buy Now often opens a "turbo checkout" popup instead of a new page
TURBO_IFRAME = '#turbo-checkout-iframe'
TURBO_PLACE_ORDER = '#turbo-checkout-pyo-button'
PRIME_NO_THANKS = [
    '#prime-interstitial-nothanks-button',
    'a:has-text("No thanks")',
    'button:has-text("No thanks")',
]


def find_visible(page: Page, selectors):
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible() and el.is_enabled():
                return el
        except Exception:
            pass
    return None


class Buyer:
    def __init__(self, notifier, auto_click_buy_now=True):
        self.notifier = notifier
        self.auto_click_buy_now = auto_click_buy_now

    def click_buy(self, page: Page) -> bool:
        btn = find_visible(page, BUY_BUTTONS)
        if btn:
            print("[Checkout] Clicking Buy Now / Pre-order...")
            btn.click(no_wait_after=True)
            return True

        btn = find_visible(page, [ADD_TO_CART])
        if btn:
            print("[Checkout] Clicking Add to Cart...")
            btn.click(no_wait_after=True)
            return True

        print("[Checkout] No buy button found.")
        return False

    def click_turbo_place_order(self, page: Page) -> bool:
        try:
            btn = page.frame_locator(TURBO_IFRAME).locator(TURBO_PLACE_ORDER)
            if btn.count() and btn.first.is_visible():
                btn.first.click(no_wait_after=True)
                return True
        except Exception:
            pass
        return False

    def place_order(self, page: Page, timeout=20) -> bool:
        """
        Polls every 100ms for whatever shows up after Buy Now (turbo popup,
        checkout page, Prime upsell, cart side sheet) and clicks through it.
        """
        deadline = time.time() + timeout
        skipped_prime = False
        clicked_ptc = False

        while time.time() < deadline:
            if self.click_turbo_place_order(page):
                print("[Checkout] Clicked 'Place your order' (popup).")
                return True

            btn = find_visible(page, PLACE_ORDER)
            if btn:
                btn.click(no_wait_after=True)
                print("[Checkout] Clicked 'Place your order'.")
                return True

            if not skipped_prime:
                btn = find_visible(page, PRIME_NO_THANKS)
                if btn:
                    print("[Checkout] Skipping Prime upsell...")
                    btn.click(no_wait_after=True)
                    skipped_prime = True

            if not clicked_ptc:
                btn = find_visible(page, PROCEED_TO_CHECKOUT)
                if btn:
                    print("[Checkout] Clicking Proceed to Checkout...")
                    btn.click(no_wait_after=True)
                    clicked_ptc = True

            page.wait_for_timeout(100)

        print("[Checkout] Could not find 'Place your order' button!")
        return False

    def confirmed(self, page: Page) -> bool:
        try:
            page.wait_for_url(lambda u: "thankyou" in u.lower() or "confirmation" in u.lower(), timeout=10000)
            return True
        except Exception:
            pass
        try:
            body = page.inner_text("body").lower()
            return "order placed" in body or "thank you" in body
        except Exception:
            return False

    def attempt_checkout(self, page: Page, product_title: str, price_str: str) -> bool:
        if not self.auto_click_buy_now:
            self.notifier.notify_in_stock(product_title, price_str, page.url)
            print("[Checkout] auto_click_buy_now is off - finish checkout in the browser.")
            return True

        start = time.time()
        clicked = self.click_buy(page)
        # Alert after clicking so it doesn't delay the click
        self.notifier.notify_in_stock(product_title, price_str, page.url)

        if not clicked or not self.place_order(page):
            self.notifier.send_desktop_notification(
                "[ACTION NEEDED] Check browser!",
                "Bot could not finish checkout. Check the browser window!"
            )
            return False

        print(f"[Checkout] Order submitted in {time.time() - start:.1f}s")
        if self.confirmed(page):
            print("[SUCCESS] ORDER PLACED!")
            self.notifier.send_desktop_notification("ORDER PLACED!", f"{product_title} - {price_str}")
        else:
            print("[Checkout] Clicked Place Order but no confirmation page seen - check the browser.")
        # Return True either way so the bot doesn't try to buy a second one
        return True

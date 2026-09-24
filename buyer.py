import sys
import time
from playwright.sync_api import Page

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

class Buyer:
    def __init__(self, notifier, auto_click_buy_now=True):
        self.notifier = notifier
        self.auto_click_buy_now = auto_click_buy_now

    def handle_prime_upsell(self, page: Page) -> bool:
        """
        If the account does not have Amazon Prime, Amazon will show a Prime upgrade page. This will detect that screen and click the 'No Thanks' button.
        """
        try:
            # Check for 'No thanks' link / button
            no_thanks = page.query_selector(
                'a:has-text("No thanks"), '
                'button:has-text("No thanks"), '
                'span:has-text("No thanks"), '
                '#prime-interstitial-nothanks-button, '
                'input[name*="noThanks" i], '
                '[data-action="page-spinner-action"]:has-text("No thanks")'
            )
            if no_thanks and no_thanks.is_visible():
                print("[Checkout] Prime upsell detected. Automatically clicking 'No thanks'...")
                no_thanks.click()
                page.wait_for_timeout(2000)
                return True

            # Fallback text locator
            no_thanks_loc = page.get_by_text("No thanks", exact=False)
            if no_thanks_loc.count() > 0 and no_thanks_loc.first.is_visible():
                print("[Checkout] Prime upsell detected via text locator. Clicking 'No thanks'...")
                no_thanks_loc.first.click()
                page.wait_for_timeout(2000)
                return True
        except Exception as e:
            print(f"[Checkout] Prime upsell bypass check: {e}")

        return False

    def attempt_checkout(self, page: Page, product_title: str, price_str: str) -> bool:
        """
        Executes automated checkout uptill the final checkout page.
        Attempts to click "Buy Now" or "Add to Card", then "Proceed to Checkout"
        Then alerts with Audio and Desktop notification
        
        """
        print("\n" + "#" * 60)
        print("[!] INITIATING RAPID CHECKOUT FLOW...")
        print("#" * 60)

        # Trigger initial notification immediately so the user can look at their screen as fast as possible
        self.notifier.notify_in_stock(product_title, price_str, page.url)

        if not self.auto_click_buy_now:
            print("[Semi-Auto] auto_click_buy_now is False. Browser is open at product page.")
            return True

        # Try 'Buy Now' button first for fastest path
        buy_now_btn = page.query_selector('#buy-now-button, input#buy-now-button')
        if buy_now_btn and buy_now_btn.is_visible() and buy_now_btn.is_enabled():
            print("[Checkout] Clicking 'Buy Now' button...")
            try:
                buy_now_btn.click()
                page.wait_for_timeout(2000)
                print("[Checkout] Buy Now triggered! Inspecting current screen...")
                # Automatically bypass Prime upgrade page if account does not have Amazon Prime
                self.handle_prime_upsell(page)
            except Exception as e:
                print(f"[Checkout] Error clicking Buy Now: {e}")

        # Fallback to Add to Cart if not on a checkout screen
        current_url = page.url.lower()
        if "checkout" not in current_url and "buy" not in current_url:
            cart_btn = page.query_selector('#add-to-cart-button, input#add-to-cart-button, #preOrderButton')
            if cart_btn and cart_btn.is_visible() and cart_btn.is_enabled():
                print("[Checkout] Clicking 'Add to Cart / Pre-order'...")
                try:
                    cart_btn.click()
                    page.wait_for_timeout(2500)
                except Exception as e:
                    print(f"[Checkout] Error clicking Add to Cart: {e}")

            # Check for side sheet checkout or cart navigation
            ptc_btn = page.query_selector(
                '#attach-sidesheet-checkout-button, '
                'input[name="proceedToRetailCheckout"], '
                '#hlb-ptc-btn-native, '
                'a[href*="proceedToCheckout"]'
            )
            if ptc_btn and ptc_btn.is_visible():
                print("[Checkout] Clicking 'Proceed to Checkout'...")
                try:
                    ptc_btn.click()
                    page.wait_for_timeout(2500)
                except Exception as e:
                    print(f"[Checkout] Error clicking Proceed to Checkout: {e}")

        # Check again in case Prime upsell appeared after cart navigation
        self.handle_prime_upsell(page)

        # Semi-automated guard: DO NOT automatically click 'Place your order'
        print("\n" + "*" * 60)
        print("[!] BOT HAS REACHED CHECKOUT SCREEN / WAITING FOR USER")
        print("[!] PLEASE CONFIRM YOUR ORDER IN THE OPEN BROWSER WINDOW")
        print("*" * 60 + "\n")

        self.notifier.send_desktop_notification(
            title="[URGENT] CHECKOUT READY!",
            message="Item has been carted! Click 'Place Your Order' in browser now!"
        )

        return True

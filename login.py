import sys
import os
import json
from browser import get_browser_context

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def main():
    print("=" * 60)
    print("Amazon.ca Session Setup / One-Time Login")
    print("=" * 60)

    # Load config if present
    config_path = "config.json"
    user_data_dir = "./amazon_profile"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8-sig") as f:
            cfg = json.load(f)
            user_data_dir = cfg.get("user_data_dir", user_data_dir)

    print(f"Profile directory: {os.path.abspath(user_data_dir)}")
    print("Opening browser window...")

    playwright, context = get_browser_context(user_data_dir=user_data_dir, headless=False)
    page = context.pages[0] if context.pages else context.new_page()

    print("\nNavigating to Amazon.ca sign-in...")
    page.goto("https://www.amazon.ca", wait_until="domcontentloaded")

    print("\n" + "="*60)
    print("[Action Required]:")
    print("1. In the browser window that just opened, sign in to your Amazon.ca account.")
    print("2. Ensure your default shipping address and 1-Click / payment settings are saved.")
    print("3. Solve any two-factor authentication (2FA/OTP) or CAPTCHA if prompted.")
    print("\nWhen you are logged in and ready, return here and press [ENTER] to save and exit.")
    print("="*60)

    input("\nPress ENTER when logged in: ")

    print("\nSaving session cookies and closing browser...")
    context.close()
    playwright.stop()
    print("Session saved successfully! The bot can now run with your authenticated account.")

if __name__ == "__main__":
    main()

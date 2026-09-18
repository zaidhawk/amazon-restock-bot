# Amazon Canada Stock Monitor & Rapid Checkout Bot

Automated checkout helper specifically configured for the Nintendo Switch 2 – The Legend of Zelda 40th Anniversary Limited Edition on Amazon.ca

---

### Step 1: One-Time Account Login 
Login to Amazon account after running login.bat:
```powershell
.\login.bat
```
*(Or run `.\venv\Scripts\python.exe login.py`)*
1. An official Chromium browser window will open to `https://www.amazon.ca`.
2. Sign in with your Amazon account, solve any 2FA/OTP code.
3. Return to the terminal and press **Enter** to save your session.

### Step 2: Start the Bot
```powershell
.\start_bot.bat
```
*(Or run `.\venv\Scripts\python.exe run.py`)*

---

You can edit `config.json` at any time to adjust parameters:

```json
{
  "product_url": "https://www.amazon.ca/Nintendo-SwitchTM-Legend-ZeldaTM-Anniversary/dp/B0HJ6F8L6V",
  "asin": "B0HJ6F8L6V",
  "product_title": "Nintendo Switch 2 - The Legend of Zelda 40th Anniversary Limited Edition",
  "max_price_cad": 720.00,
  "check_interval_seconds_min": 5,
  "check_interval_seconds_max": 10,
  "user_data_dir": "./amazon_profile",
  "headless": false,
  "auto_click_buy_now": true,
  "only_ships_from_amazon": true,
  "sound_alert_duration_seconds": 30
}
```

### Safety Features
- **Max Price Filter (`max_price_cad`)**: Prevents buying from a third party seller attempting to scalp.
- **Retailer Filter (`only_ships_from_amazon`)**: Filters out third-party marketplace sellers so you only buy directly from Amazon.ca.
- **Semi-Automated Checkout (`auto_click_buy_now`)**: Automatically clicks "Buy Now" or "Add to Cart" -> "Proceed to Checkout", then halts at the order review screen for you to confirm and place your order.
- **Jittered Polling**: Randomizes request delays (5-10s) and hides automation markers to prevent anti-bot detection.

---

## Notifications
When stock drops:
1. **Audio Alarm**: Plays an alarm on Windows speakers..
2. **Windows Notification**: Displays a notification with the detected price.
3. **Active Checkout**: Brings the browser to the front with the item ready for confirmation.

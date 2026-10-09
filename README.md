# Amazon Restock Bot

A bot that watches an Amazon.ca product page and buys it automatically as soon as it comes back in stock.

## 1. Log in (one time only)

Run `login.bat`. A browser window will open. Sign in to your Amazon account, then go back to the terminal and press Enter. Your login is saved, so you only need to do this once.

## 2. Start the bot

Run `start_bot.bat`. The bot will keep checking the product page and place the order when it's in stock.

## Choosing a product

Open `config.json` and paste the Amazon link of the product you want into `product_url`:

```json
"product_url": "https://www.amazon.ca/your-product-link"
```

Also set `max_price_cad` to the most you're willing to pay, so the bot won't buy from a scalper.

# arb-bot

Arbitrage bot for trading LTC-ETH across Binance and GDAX. The script runs in an infinite loop, pulling ticker prices from GDAX and Binance to identify discrepancies and execute trades based on a user-defined margin.

## Getting Started

To get started, you will need a [Binance](https://www.binance.com/?ref=12918385) account and a [Coinbase/GDAX](https://www.coinbase.com/join/59d5484d4f1501012ea9998a) account. Set up API keys for each of these - paste these keys and secrets in the appropriate blanks in the code. You will also need a GDAX LTC deposit address to paste in to the code (you can get this by clicking on deposit on the left-hand side of LTC/USD). 

The bot will use all available USD funds in your GDAX account. Pre-load this with as much as you'd like to let the bot use - anything over $200-$300 will be functional.

### Installing

To install prerequisites, simply run:

```
pip install -r requirements.txt
```

To execute the program after having filled in the appropriate keys from the previous step, run:
```
python arb_bot_public.py
```

You will be asked to enter an minimum arbitrage margin - this should be > 1.00, with 1.05 representing a 5% margin. The greater the value, the less frequent the bot will be triggered to trade, but the less risky the trade will be.

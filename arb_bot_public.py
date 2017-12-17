from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceWithdrawException

import json
import gdax
import time
import decimal 
import requests
import datetime

api_key = "<FILL IN BINANCE KEY>"
api_secret = "<BINANCE SECRET"
binance_client = Client(api_key, api_secret)

gdax_key = "<GDAX KEY>"
gdax_secret = "<GDAX SECRET>"
gdax_pass = "<GDAX PASS>"
gdax_client = gdax.AuthenticatedClient(gdax_key, gdax_secret, gdax_pass)

# Returns a floating point representation of how much currency we have available
def get_binance_free_balance(ticker):
	binance_account_info = binance_client.get_account()
	balances = binance_account_info['balances']
	for entry in balances:
		if entry['asset'] == ticker:
			return float(entry['free'])
	return 'Ticker not found.'		

def get_gdax_free_balance(ticker):
	balances = gdax_client.get_accounts()	
	for entry in balances:
		if entry['currency'] == ticker:
			return float(entry['available'])
	return 'Ticker not found.'

def wait_for_order(id):
	status = 'pending'
	while(status != 'done'):
		try:
			status = gdax_client.get_order(id)['status']
		except Exception:
			continue
		time.sleep(2)

def do_arb_trade():
	print("Executing arb trade. Start time: " + str(datetime.datetime.now()))
	# buy ETH for USD in GDAX
	gdax_ethusd = gdax_client.get_product_ticker(product_id='ETH-USD')['price']
	g_usd_qty = get_gdax_free_balance('USD') 
	g_eth_purchase_qty = "{0:.3f}".format((g_usd_qty - 1.0) / float(gdax_ethusd))
	print(g_eth_purchase_qty)
	print("Starting GDAX USD balance: {}".format(g_usd_qty))
	g_buy = gdax_client.buy(price=gdax_ethusd, #USD
               size=g_eth_purchase_qty, #ETH
               product_id='ETH-USD')
	print(g_buy)
	wait_for_order(g_buy['id'])	
	# transfer ETH to Binance
	g_eth_balance = get_gdax_free_balance('ETH')
	print("Starting GDAX ETH balance: {}".format(g_eth_balance))
	# Get binance deposit address
	b_deposit_address = None
	while (b_deposit_address is None):
		try:
			b_deposit_address = binance_client.get_deposit_address(asset='ETH')['address']
		except requests.ConnectionError:
			continue
		time.sleep(1)	
	# Make GDAX withdrawal request to Binance		
	g_withdraw = gdax_client.crypto_withdraw(amount=g_eth_balance, 
			currency='ETH', 
			crypto_address=b_deposit_address)
	print(g_withdraw)

	b_orig_deposits = binance_client.get_deposit_history()['depositList']
	print("Transferring ETH to Binance...")
	# Wait for new deposit transaction to post on Binance with non-pending status
	b_new_deposits = b_orig_deposits
	while ((b_new_deposits == b_orig_deposits) or (b_new_deposits[0]['status'] == 0)):
		try:
			b_new_deposits = binance_client.get_deposit_history()['depositList']
		except requests.ConnectionError:
			continue
		time.sleep(60)
	b_new_eth_balance = get_binance_free_balance('ETH')
	print("New Binance ETH balance: {}".format(b_new_eth_balance))
	# Market buy LTC with ETH on Binance
	b_ltceth = None
	while b_ltceth is None:
		try:
			b_ltceth = binance_client.get_symbol_ticker(symbol='LTCETH')['price']
		except Exception:
			continue
		time.sleep(1)
	b_ltc_qty = float(b_new_eth_balance) / float(b_ltceth)
	b_ltc_qty = decimal.Decimal(b_ltc_qty).quantize(decimal.Decimal('.01'), rounding=decimal.ROUND_DOWN)

	b_order = binance_client.order_market_buy(
	    symbol='LTCETH',
	    quantity=b_ltc_qty)
	print(b_order)
	# transfer LTC to GDAX
	g_orig_ltc_balance = get_gdax_free_balance('LTC')
	b_ltc_balance = get_binance_free_balance('LTC')
	print("Purchased Binance LTC balance: {}".format(b_ltc_balance))
	try:
	    result = binance_client.withdraw(
	    	name='gdax',
	        asset='LTC',
	        address='<GDAX LTC ADDRESS HERE>',
	        amount=b_ltc_balance,
	        recvWindow=6000000)
	except BinanceAPIException as e:
	    print(e)
	except BinanceWithdrawException as e:
	    print(e)
	else:
	    print("Binance withdrawal of LTC to GDAX successful.")

	# sell LTC for USD on GDAX
	print("Transferring LTC to GDAX...")
	while (get_gdax_free_balance('LTC') <= g_orig_ltc_balance):
		time.sleep(60)

	gdax_ltcusd = gdax_client.get_product_ticker(product_id='LTC-USD')['price']
	g_ltc_qty = get_gdax_free_balance('LTC')
	print("Received GDAX LTC balance: {}".format(g_ltc_qty))
	g_order = gdax_client.sell(price=gdax_ltcusd, #ETH
	                size=g_ltc_qty, #LTC
	                product_id='LTC-USD')
	print(g_order)
	wait_for_order(g_order['id'])
	print("Sold {} LTC for USD @ {}.".format(g_ltc_qty, gdax_ltcusd))
	g_usd_qty = get_gdax_free_balance('USD')
	print("Ending GDAX USD balance: {}".format(g_usd_qty))
	print("Ending arb trade. End time: " + str(datetime.datetime.now()))

ratio = float(input('Enter desired arbitrage margin (i.e. 1.02 for 2%): '))
# do_arb_trade()
while True:
	binance_ltceth = binance_client.get_symbol_ticker(symbol='LTCETH')['price']
	# check ltc -> usd -> eth
	gdax_ltceth = float(gdax_client.get_product_ticker(product_id='LTC-USD')['price']) / float(gdax_client.get_product_ticker(product_id='ETH-USD')['price'])
	g_b_ratio = float(gdax_ltceth) / float(binance_ltceth)
	if g_b_ratio > ratio:
		print("LTC-ETH arbitrage opportunity detected. \nGDAX price: {}. \nBinance price: {}. \nProfit margin: {}".format(gdax_ltceth, binance_ltceth, g_b_ratio))
		do_arb_trade()
	else:
		print("No LTC-ETH arbitrage opportunity detected. \nGDAX price: {}. \nBinance price: {}. \nProfit margin: {}".format(gdax_ltceth, binance_ltceth, g_b_ratio))
	time.sleep(15)	


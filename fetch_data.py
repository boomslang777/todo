from ib_insync import *
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Create an instance of the IB class
ib = IB()

# Connect to the IB server
ib.connect('127.0.0.1', 7497, clientId=1)
banknifty = Index('BANKNIFTY','NSE','INR')
ib.qualifyContracts(banknifty)
ib.reqMarketDataType(4)
[ticker] = ib.reqTickers(banknifty)
print(ticker.marketPrice())




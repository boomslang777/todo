from ib_insync import *
import pandas as pd
import time
import csv
# import logging
# logging.basicConfig(level=logging.INFO)
def cancel_all_open_orders():
    for trade in ib.openTrades():
        ib.cancelOrder(trade.order)

def round_to_nearest(value, increment):
    return round(value / increment) * increment
def close_open_positions():
    possy = ib.portfolio()
    print(possy)
    for pos in possy :
        contract = pos.contract
        if contract.secType == 'STK' :
            if pos.position > 0 :
                action = 'SELL'
                sqoff = Stock(pos.contract.symbol,"SMART",pos.contract.currency)
                ib.qualifyContracts(sqoff)
            elif pos.position < 0 :
                action = 'BUY'
                sqoff = Stock(pos.contract.symbol,"SMART",pos.contract.currency)
                ib.qualifyContracts(sqoff)
        elif contract.secType == 'OPT':
            if pos.position > 0 :
                action = 'SELL'
                sqoff = Option(pos.contract.symbol,pos.contract.lastTradeDateOrContractMonth,pos.contract.strike,pos.contract.right,"SMART",pos.contract.multiplier,pos.contract.currency)
                ib.qualifyContracts(sqoff)
            elif pos.position < 0 :
                action = 'BUY'
                sqoff = Option(pos.contract.symbol,pos.contract.lastTradeDateOrContractMonth,pos.contract.strike,pos.contract.right,"SMART",pos.contract.multiplier,pos.contract.currency)
                ib.qualifyContracts(sqoff)
        Order = MarketOrder(action, abs(pos.position))
        ib.placeOrder(sqoff, Order)
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=225)
close_open_positions()
spx = Index('SPX', 'CBOE')
ib.qualifyContracts(spx)
cds = ib.reqContractDetails(spx)
ib.reqMarketDataType(1)
[ticker] = ib.reqTickers(spx)
spxValue = ticker.marketPrice()
print(spxValue)
chains = ib.reqSecDefOptParams(spx.symbol, '', spx.secType, spx.conId)

util.df(chains)
chain = next(c for c in chains if c.tradingClass == 'SPXW' and c.exchange == 'SMART')


# Assuming you want contracts for the first expiration date
strikes = [strike for strike in chain.strikes
           if strike % 5 == 0
           and spxValue - 100 < strike < spxValue + 100]
expirations = sorted(exp for exp in chain.expirations)[:3]
rights = ['P', 'C']

# Filter contracts based on a specific expiration
desired_expiration = expirations[0]  # Change this to the desired expiration date
contracts = [Option('SPX', desired_expiration, strike, right, 'SMART')
             for right in rights
             for strike in strikes]
Option()
contracts = ib.qualifyContracts(*contracts)
print(len(contracts))
tickers = ib.reqTickers(*contracts)
call_deltas = [0.05, 0.1]
put_deltas = [-0.05, -0.1]

# Filter call and put tickers based on delta conditions
call_tickers = [ticker for ticker in tickers if ticker.contract.right == 'C' and call_deltas[0] < ticker.modelGreeks.delta < call_deltas[1]]
put_tickers = [ticker for ticker in tickers if ticker.contract.right == 'P' and put_deltas[0] > ticker.modelGreeks.delta > put_deltas[1]]

# Check if the lists are not empty before finding the maximum
max_ltp_call = max(call_tickers, key=lambda ticker: ticker.last, default=None)
max_ltp_put = max(put_tickers, key=lambda ticker: ticker.last, default=None)

# Return the strikes of the calls and puts with maximum LTP if they exist
if max_ltp_call:
    max_ltp_call_strike = max_ltp_call.contract.strike
    print(f"Strike of Call with Max LTP: {max_ltp_call_strike}")
else:
    print("No eligible call options found.")

if max_ltp_put:
    max_ltp_put_strike = max_ltp_put.contract.strike
    print(f"Strike of Put with Max LTP: {max_ltp_put_strike}")
else:
    print("No eligible put options found.")

offset = 30

# Store short put and short call contracts in a list
short_put_contract = max_ltp_put.contract
short_call_contract = max_ltp_call.contract
short_contracts = [short_put_contract, short_call_contract]

# Qualify the short contracts using ib.qualifyContracts
ib.qualifyContracts(*short_contracts)

# Now, qualify the long put and long call contracts
long_put_contract = Contract()
long_put_contract.symbol = short_put_contract.symbol
long_put_contract.secType = short_put_contract.secType
long_put_contract.lastTradeDateOrContractMonth = short_put_contract.lastTradeDateOrContractMonth
long_put_contract.strike = short_put_contract.strike - offset
long_put_contract.right = 'P'  # Put option
long_put_contract.exchange = short_put_contract.exchange

long_call_contract = Contract()
long_call_contract.symbol = short_call_contract.symbol
long_call_contract.secType = short_call_contract.secType
long_call_contract.lastTradeDateOrContractMonth = short_call_contract.lastTradeDateOrContractMonth
long_call_contract.strike = short_call_contract.strike + offset
long_call_contract.right = 'C'  # Call option
long_call_contract.exchange = short_call_contract.exchange

# Use ib.qualifyContracts to get additional contract details for the long contracts
ib.qualifyContracts(long_put_contract, long_call_contract)

# Now you have qualified contracts for both short and long options
print("Qualified Short Put Contract:", short_put_contract)
print("Qualified Long Put Contract:", long_put_contract)
print("Qualified Short Call Contract:", short_call_contract)
print("Qualified Long Call Contract:", long_call_contract)    
short_put_md = ib.reqTickers(short_put_contract)[0]
short_call_md = ib.reqTickers(short_call_contract)[0]
long_put_md = ib.reqTickers(long_put_contract)[0]
long_call_md = ib.reqTickers(long_call_contract)[0]
short_put_greeks = short_put_md.modelGreeks
short_call_greeks = short_call_md.modelGreeks
long_put_greeks = long_put_md.modelGreeks
long_call_greeks = long_call_md.modelGreeks

# Creating a list of dictionaries for each contract
contracts_data = [
    {'Contract': 'Short Put', 'Strike': short_put_contract.strike,
     'Delta': short_put_greeks.delta, 'Vega': short_put_greeks.vega,
     'Gamma': short_put_greeks.gamma, 'Theta': short_put_greeks.theta,
     'IV': short_put_greeks.impliedVol},
    
    {'Contract': 'Short Call', 'Strike': short_call_contract.strike,
     'Delta': short_call_greeks.delta, 'Vega': short_call_greeks.vega,
     'Gamma': short_call_greeks.gamma, 'Theta': short_call_greeks.theta,
     'IV': short_call_greeks.impliedVol},
    
    {'Contract': 'Long Put', 'Strike': long_put_contract.strike,
     'Delta': long_put_greeks.delta, 'Vega': long_put_greeks.vega,
     'Gamma': long_put_greeks.gamma, 'Theta': long_put_greeks.theta,
     'IV': long_put_greeks.impliedVol},
    
    {'Contract': 'Long Call', 'Strike': long_call_contract.strike,
     'Delta': long_call_greeks.delta, 'Vega': long_call_greeks.vega,
     'Gamma': long_call_greeks.gamma, 'Theta': long_call_greeks.theta,
     'IV': long_call_greeks.impliedVol},
]

# Writing the data to a CSV file
csv_file_path = 'greeks_data.csv'
with open(csv_file_path, 'w', newline='') as csv_file:
    fieldnames = ['Contract', 'Strike', 'Delta', 'Vega', 'Gamma', 'Theta', 'IV']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    
    # Writing the header
    writer.writeheader()
    
    # Writing the data
    writer.writerows(contracts_data)

print(f"Greeks data saved to {csv_file_path}")

print(f"Greeks data saved to {csv_file_path}")
combo = Contract(
    secType='BAG',
    symbol='SPX',
    exchange='SMART',
    currency='USD',
#   tradingClass='SPXW',
    comboLegs=[
        ComboLeg(
            conId=short_put_contract.conId,
            ratio=1,
            action='SELL',
            exchange='SMART'),
        ComboLeg(
            conId=long_put_contract.conId,
            ratio=1,
            action='BUY',
            exchange='SMART'),
        ComboLeg(
            conId=short_call_contract.conId,
            ratio=1,
            action='SELL',
            exchange='SMART'),
        ComboLeg(
            conId=long_call_contract.conId,
            ratio=1,
            action='BUY',
            exchange='SMART'),       
    ])
order = MarketOrder(action='SELL', totalQuantity=1, orderRef='condor')
trade = ib.placeOrder(combo, order)
ib.sleep(5)
time.sleep(5)
fill = trade.orderStatus.avgFillPrice
print(f"{fill} is average fill price ")
ib.sleep(5)
while True :
    ltp = ib.reqMktData(combo, '', False, False).marketPrice()
    print(f"{ltp} is the last traded price")
    if ltp < fill - 0.05 :
        od = LimitOrder(action = 'BUY',totalQuantity = 1,orderRef='Condor close',lmtPrice = ltp-0.06)
    elif ltp < fill - 0.15 :
        cancel_all_open_orders()
        close_open_positions()    
    ib.sleep(5)



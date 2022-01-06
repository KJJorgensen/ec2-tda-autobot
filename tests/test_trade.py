from fastapilib import trade

data = {'ticker': 'RCL', 'close': 68.17, 'quantity': 2, 'dte': 30, 'callput': 'CALL', 'instruction': 'BUY_TO_OPEN', 'passphrase': 'SScamaro98'}

res = trade.main(data)

print(f'result: {res}')
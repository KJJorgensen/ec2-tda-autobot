from tda import auth
import os
from fastapilib import config
import json

token_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ameritrade_credentials.json')
api_key = config.api_key
c = auth.client_from_token_file(token_path, api_key)

fields = c.Account.Fields('positions')
response = c.get_account(config.account_id, fields = fields)
r = json.load(response)
#print(r)
pos_dict = {}
for i in r['securitiesAccount']['positions']:
    symbol = i['instrument']['underlyingSymbol']
    opt_symbol = i['instrument']['symbol']
    close_quantity = i['settledLongQuantity'] + i['settledShortQuantity']
    pos_dict[symbol] = [opt_symbol, close_quantity]
print(pos_dict)

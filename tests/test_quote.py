from tda import auth
import os
from fastapilib import config
import json

token_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ameritrade_credentials.json')
api_key = config.api_key
c = auth.client_from_token_file(token_path, api_key)


symbol = 'TME_010722P4.5' #add a current position here
r = c.get_quote(symbol).json()
print(r)